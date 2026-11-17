import json,math,hashlib
from pathlib import Path
import numpy as np,ezdxf,ifcopenshell
from ifcopenshell.util import placement,system
from shapely.geometry import LineString,Point,Polygon,box
from shapely.strtree import STRtree
from ezdxf.path import make_path
from bsa.cad_text_layout import text_box
from outlet_native_batches import bounds,body,matrix
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'logical-equipment-network';S=B/'three-dimensional-outlet-candidate';O=R/'drawing';O.mkdir(exist_ok=False);p=R/'Supply Air Logical Network.ifc';m=ifcopenshell.open(str(p));integration=json.loads((R/'integration.json').read_text());prior=json.loads((S/'drawing-readable-screened/projection.json').read_text());offset=np.array(prior['common_xy_translation_m']);d=ezdxf.readfile(S/'drawing-readable-screened/Supply and Three Dimensional Branch Connections.dxf');ms=d.modelspace();d.linetypes.new('BSA_LOGICAL_DASHED',dxfattribs={'description':'Logical equipment flow mapping','pattern':[.24,.12,-.12]})
for layer,col,lt in [('BSA_EQUIPMENT_ENVELOPE',8,'Continuous'),('BSA_LOGICAL_DEVICE_AXIS',8,'BSA_LOGICAL_DASHED'),('BSA_REDUCER_MATERIAL',7,'Continuous')]:d.layers.new(layer,dxfattribs={'color':col,'linetype':lt})
def line(a,b,guid):
 e=ms.add_line(tuple(np.asarray(a)[:2]+offset),tuple(np.asarray(b)[:2]+offset),dxfattribs={'layer':'BSA_LOGICAL_DEVICE_AXIS'});e.set_xdata('BSA_IFC',[(1000,guid)])
for row in integration['records']:
 for g in [row['vav_guid'],row['plenum_guid']]:
  lo,hi=bounds(body(m.by_guid(g)),matrix(m.by_guid(g)));xy=[lo[:2],[hi[0],lo[1]],hi[:2],[lo[0],hi[1]]];e=ms.add_lwpolyline([tuple(np.asarray(q)+offset) for q in xy],close=True,dxfattribs={'layer':'BSA_EQUIPMENT_ENVELOPE'});e.set_xdata('BSA_IFC',[(1000,g)])
 points={k:placement.get_local_placement(m.by_guid(row[k]).ObjectPlacement)[:3,3] for k in ['vav_inlet_guid','vav_outlet_guid','plenum_inlet_guid']};line(points['vav_inlet_guid'],points['vav_outlet_guid'],row['vav_guid']);axis=placement.get_local_placement(m.by_guid(row['vav_outlet_guid']).ObjectPlacement)[:3,2];W=next(x for x in integration['records'] if x['id']==row['id']);lo,hi=bounds(body(m.by_guid(row['plenum_guid'])),matrix(m.by_guid(row['plenum_guid'])));centre=(lo+hi)/2;end=centre+axis*(36*.0254/2);line(points['plenum_inlet_guid'],end,row['plenum_guid'])
 for outlet in row['outlets']:
  port=m.by_guid(outlet['port_guid']);f=placement.get_local_placement(port.ObjectPlacement);q=f[:3,3];u=f[:3,2];projection=centre+axis*((q-centre)@axis);line(projection,q,row['plenum_guid']);reducer=m.by_guid(outlet['reducer_guid']);solid=reducer.Representation.Representations[0].Items[0];profile=[np.array(t.Coordinates) for t in solid.SweptArea.OuterCurve.Points];assert np.array_equal(profile[0],profile[-1]);origin=placement.get_local_placement(m.by_guid(outlet['reducer_inlet_guid']).ObjectPlacement)[:3,3];normal=np.array([-u[1],u[0],0.])
  for sign in [-1,1]:
   xy=[(origin+u*t[1]+normal*sign*t[0])[:2]+offset for t in profile[:-1]];e=ms.add_lwpolyline([tuple(t) for t in xy],close=True,dxfattribs={'layer':'BSA_REDUCER_MATERIAL'});e.set_xdata('BSA_IFC',[(1000,reducer.GlobalId)])
 for e in ms.query('TEXT'):
  if e.dxf.layer=='BSA_VAV_LABEL' and e.dxf.text==row['id']:e.set_xdata('BSA_IFC',[(1000,row['vav_guid'])])
for e in ms.query('TEXT'):
 t=e.dxf.text
 if t.startswith('SUPPLY AND 3D'):e.dxf.text='LOGICAL SUPPLY NETWORK TO 80 TERMINAL CONNECTIONS'
 elif t.startswith('Saved main material'):e.dxf.text='Main/reducer material sections + branch axes + equipment envelopes | 1:200'
 elif t.startswith('164main bodies'):e.dxf.text='One logical tree;1287ports;603interfaces;physical equipment airways unverified'
 elif t.startswith('Branch proxy:'):e.dxf.text='Equipment outlines: outside envelopes;dashed lines:logical flow,internal routing unknown'
 elif t.startswith('Main114conditional'):e.dxf.text='194conditional values;264unknown component paths;drop304.8mmassumed;full pressure unresolved'
# Place labels with existing measured font boxes and actual figure obstacles.
graphics=[];reserved=[];terminals={r['terminal']:np.array(r['actual_terminal_point_m'])[:2]+offset for r in prior['records']};vavs={row['id']:placement.get_local_placement(m.by_guid(row['vav_inlet_guid']).ObjectPlacement)[:2,3]+offset for row in integration['records']}
for e in ms:
 if e.dxftype()=='LINE':graphics.append(LineString([tuple(e.dxf.start)[:2],tuple(e.dxf.end)[:2]]))
 elif e.dxftype()=='LWPOLYLINE':
  pts=[tuple(v)[:2] for v in make_path(e).flattening(.02)];graphics.append(Polygon(pts) if e.dxf.layer=='BSA_EQUIPMENT_ENVELOPE' else LineString(pts))
 elif e.dxftype()=='CIRCLE':graphics.append(Point(tuple(e.dxf.center)[:2]).buffer(e.dxf.radius))
 elif e.dxftype()=='TEXT' and e.dxf.layer not in ['BSA_BRANCH_LABEL','BSA_VAV_LABEL']:reserved.append(box(*text_box(e)).buffer(.06))
tree=STRtree(graphics);placed=[];labelrecords=[]
for layer,anchors in [('BSA_VAV_LABEL',vavs),('BSA_BRANCH_LABEL',terminals)]:
 for e in sorted([e for e in ms.query('TEXT') if e.dxf.layer==layer],key=lambda e:e.dxf.text):
  e.dxf.height=.36;anchor=anchors[e.dxf.text];bb=text_box(e);oldcentre=(bb[:2]+bb[2:])/2;size=bb[2:]-bb[:2];chosen=None
  for distance in [.5,.65,.8,1.,1.2,1.4,1.6,1.8,2.]:
   for k in [4,12,0,8,2,6,14,10,1,3,5,7,9,11,13,15]:
    target=anchor+distance*np.array([math.cos(k*math.pi/8),math.sin(k*math.pi/8)]);lo=target-size/2;hi=target+size/2;polygon=box(*lo,*hi).buffer(.06)
    if lo[0]<.1 or hi[0]>57.9 or lo[1]<3.5 or hi[1]>33.5 or len(tree.query(polygon,predicate='intersects')) or any(polygon.intersects(x) for x in reserved+placed):continue
    if any(np.linalg.norm(target-other)<=distance+.1 for name,other in anchors.items() if name!=e.dxf.text):continue
    chosen=target;placed.append(polygon);break
   if chosen is not None:break
  assert chosen is not None,e.dxf.text;delta=chosen-oldcentre;e.dxf.insert=(e.dxf.insert.x+delta[0],e.dxf.insert.y+delta[1],0.);labelrecords.append(dict(label=e.dxf.text,anchor_m=anchor.tolist(),centre_m=chosen.tolist()))
assert len(labelrecords)==100;dxf=O/'Supply Air Logical Network.dxf';d.saveas(dxf);source_sheet=json.loads((S/'drawing-readable-screened/sheet.json').read_text());source_sheet['source']='Saved664elementcandidate:main/reducer material,branchaxes,equipmentenvelopes andlogicalflowmapping';(O/'sheet.json').write_text(json.dumps(source_sheet,indent=2));projection=dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),routes=prior['records'],common_xy_translation_m=offset.tolist(),equipment_envelopes=40,reducer_material_products=80,logical_flow_axes_are_schematic=True,label_count=100,label_graphics_screen_pass=True,label_records=labelrecords,native_reopen_pass=False,actual_visual_review='pending',design_accepted=False);(O/'projection.json').write_text(json.dumps(projection,indent=2));print('40equipment envelopes/80reducer sections/100labels prepared')
