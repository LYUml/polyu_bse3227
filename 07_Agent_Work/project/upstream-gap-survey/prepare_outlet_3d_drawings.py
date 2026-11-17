import json,math,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom,ezdxf,trimesh
from ifcopenshell.util import placement
from bsa.circular_geometry import configure
from bsa.round_bend_quantities import calculate
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';O=R/'drawing-reviewed';O.mkdir(exist_ok=False);S=B/'equal-cross-compound-core-candidate';source=R/'Supply and Three Dimensional Outlet Candidate.ifc';m=ifcopenshell.open(str(source));review=json.loads((R/'review.json').read_text());doc=ezdxf.readfile(S/'drawing-pressure-reviewed/Supply Network with Constant Junction Core.dxf');main=ifcopenshell.open(str(S/'Supply Network.ifc'));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);configure(settings);ms=doc.modelspace()
ref=next(e for e in ms if e.dxftype()=='LINE' and e.dxf.layer=='BSA_MATERIAL_SECTION');guid=ref.get_xdata('BSA_IFC')[0].value
saved=np.array([list(p)[:2] for e in ms if e.dxftype()=='LINE' and e.dxf.layer=='BSA_MATERIAL_SECTION' and e.get_xdata('BSA_IFC')[0].value==guid for p in [e.dxf.start,e.dxf.end]])
shape=ifcopenshell.geom.create_shape(settings,main.by_guid(guid));mesh=trimesh.Trimesh(vertices=np.asarray(shape.geometry.verts).reshape(-1,3),faces=np.asarray(shape.geometry.faces).reshape(-1,3),process=False);cut=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,0]);native=cut.reshape(-1,3)[:,:2];offset=saved.min(axis=0)-native.min(axis=0);assert np.allclose(saved.max(axis=0)-native.max(axis=0),offset,atol=1e-9,rtol=0)
for layer,color in [('BSA_BRANCH_AXIS',5),('BSA_TERMINAL_CENTRE',3),('BSA_BRANCH_LABEL',3)]:doc.layers.new(layer,dxfattribs={'color':color})
records=[]
for r in review['records']:
 parts=r['pieces'];lead,bend,tangent,down=parts;actual=[]
 for p in parts:
  obj=m.by_guid(p['guid']);ports={x.Name:x for x in __import__('ifcopenshell.util.system',fromlist=['get_ports']).get_ports(obj)};start=placement.get_local_placement(ports['inlet'].ObjectPlacement)[:3,3];end=placement.get_local_placement(ports['outlet'].ObjectPlacement)[:3,3];assert np.allclose(start,p['start_m'],atol=1e-9,rtol=0) and np.allclose(end,p['end_m'],atol=1e-9,rtol=0);actual.append((start,end))
 geo=calculate(m.by_guid(bend['guid']));a,b=actual[1];c=np.array(bend['centre_m']);sgn=np.sign((a[0]-c[0])*(b[1]-c[1])-(a[1]-c[1])*(b[0]-c[0]));bulge=float(sgn*math.tan(geo['angle_rad']/4));pts=[actual[0][0],actual[0][1],actual[1][1],actual[2][1],actual[3][1]];data=[(*tuple(p[:2]+offset),bulge if i==1 else 0.) for i,p in enumerate(pts)];e=ms.add_lwpolyline(data,format='xyb',dxfattribs={'layer':'BSA_BRANCH_AXIS'});e.set_xdata('BSA_IFC',[(1000,p['guid']) for p in parts]);T=pts[-1][:2]+offset;circle=ms.add_circle(T,.15,dxfattribs={'layer':'BSA_TERMINAL_CENTRE'});circle.set_xdata('BSA_IFC',[(1000,down['guid'])]);label=ms.add_text(r['terminal'],dxfattribs={'height':.32,'insert':tuple(T+[.2,.15]),'layer':'BSA_BRANCH_LABEL'});label.set_xdata('BSA_IFC',[(1000,down['guid'])]);records.append(dict(terminal=r['terminal'],polyline_handle=e.dxf.handle,terminal_marker_handle=circle.dxf.handle,guids=[p['guid'] for p in parts],actual_terminal_point_m=pts[-1].tolist()))
for e in ms:
 if e.dxftype()!='TEXT' or e.dxf.layer=='BSA_BRANCH_LABEL':continue
 t=e.dxf.text
 if t.startswith('SUPPLY NETWORK'):e.dxf.text='SUPPLY AND 3D BRANCH CONNECTION CANDIDATE'
 elif t.startswith('Actual saved horizontal'):e.dxf.text='Saved main material section + actual branch-axis plan projection | 1:200'
 elif t.startswith('164 bodies;'):e.dxf.text='164main bodies +320branch pieces;80terminal turns;equipment internal flow unconnected'
 elif t.startswith('Nominal profiles'):e.dxf.text='Branch proxy: nominal8in,R=1.5D,304.8mm drop ASSUMED;actual ceiling/neck height unknown'
 elif t.startswith('VAV internals'):e.dxf.text='Main114conditional/4gaps only;branch product,bend losses,installation and full pressure unresolved'
p=O/'Supply and Three Dimensional Branch Connections.dxf';doc.saveas(p);sheet=json.loads((S/'drawing-pressure-reviewed/sheet.json').read_text());sheet['source']='Actual164mainmaterialsection +320savedbranchAxis projection,80assumedlowerterminalcentres';(O/'sheet.json').write_text(json.dumps(sheet,indent=2));(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),main_products=164,branch_products=320,route_count=80,records=records,common_xy_translation_m=offset.tolist(),native_reopen_pass=False,visual_review='pending',design_accepted=False),indent=2));print('80actual saved route axes projected;native runpending')
# Actual material side section of longest route tangent and terminal quarter.
r=max(review['records'],key=lambda r:r['branch_centreline_m']);parts=r['pieces'][-2:];origin=np.array(parts[0]['start_m']);u=np.array(parts[0]['start_tangent']);normal=np.cross(u,[0,0,1]);d=ezdxf.new('R2018');d.units=6;d.appids.new('BSA_IFC');dm=d.modelspace();segments=[]
for part in parts:
 obj=m.by_guid(part['guid']);shape=ifcopenshell.geom.create_shape(settings,obj);mesh=trimesh.Trimesh(vertices=np.asarray(shape.geometry.verts).reshape(-1,3),faces=np.asarray(shape.geometry.faces).reshape(-1,3),process=False);cut=trimesh.intersections.mesh_plane(mesh,normal,origin);assert len(cut);xy=np.stack([(cut-origin)@u,(cut-origin)@np.array([0,0,1])],axis=-1);segments.append((obj.GlobalId,xy))
for layer in ['BSA_DETAIL_CUT','BSA_DETAIL_NOTES','BSA_SECTION_REFERENCE']:d.layers.new(layer)
pts=np.concatenate([xy.reshape(-1,2) for _,xy in segments]);off=np.array([.2,.8])-pts.min(axis=0)
for guid,segs in segments:
 for seg in segs:
  if np.linalg.norm(seg[1]-seg[0])<1e-10:continue
  e=dm.add_line(tuple(seg[0]+off),tuple(seg[1]+off),dxfattribs={'layer':'BSA_DETAIL_CUT'});e.set_xdata('BSA_IFC',[(1000,guid)])
texts=[('TERMINAL TURN CONNECTION DETAIL',2.88,.09),(r['terminal']+' | actual native material section | 1:15',2.6,.045),('Nominal8in;R304.8mm;source terminal XY preserved;assumed drop304.8mm',.48,.03),('Smooth rigid-equivalent proxy;actual heights,joints,flex product and pressures unverified',.31,.03)]
for t,y,h in texts:dm.add_text(t,dxfattribs={'height':h,'insert':(.15,y),'layer':'BSA_DETAIL_NOTES'})
e=dm.add_line((.15,.16),(.65,.16),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,parts[-1]['guid'])]);dm.add_text('0.5m reference',dxfattribs={'height':.025,'insert':(.75,.15),'layer':'BSA_DETAIL_NOTES'})
Q=R/'detail-reviewed';Q.mkdir(exist_ok=False);d.saveas(Q/'Terminal Turn Connection Detail.dxf');settings=dict(source='Actual longest branch tangent and downwardquarter material section,assumedheights',window_drawing_units=[0,0,4.35,3.],scale_denominator=15,reference_ifc_guid=parts[-1]['guid'],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(Q/'sheet.json').write_text(json.dumps(settings,indent=2));(Q/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),terminal=r['terminal'],source_guids=[p['guid'] for p in parts],native_reopen_pass=False,visual_review='pending',design_accepted=False),indent=2));print('Actualterminalsidecutprepared')
