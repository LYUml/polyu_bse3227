"""Actual native side cuts make the height change reviewable in CAD."""
from pathlib import Path
import json,hashlib
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh,ezdxf
from ifcopenshell.util.placement import get_local_placement
from bsa.ifc_native import run
from bsa.duct_transition_quantities import calculate
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/constant-height-tee-network');O=R/'details';O.mkdir(exist_ok=False);source=R/'Supply Network.ifc';m=ifcopenshell.open(str(source));cases=json.loads((R/'integration.json').read_text())['cases'];flows=json.loads((R/'flow-review.json').read_text());settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
d=ezdxf.new('R2018');d.units=6;d.appids.new('BSA_IFC');ms=d.modelspace()
for layer in ['NATIVE_SIDE_CUT','DETAIL_NOTES','DETAIL_REFERENCE']:d.layers.new(layer)
counts={};labels=[]
for index,r in enumerate(cases):
 tee=m.by_guid(r['tee_guid']);trans=m.by_guid(r['transition_guid']);frame=get_local_placement(m.by_guid(r['branch_port_guid']).ObjectPlacement);origin=get_local_placement(tee.ObjectPlacement)[:3,3];segments=[]
 for obj in [tee,trans]:
  shape=ifcopenshell.geom.create_shape(settings,obj);v=np.asarray(shape.geometry.verts).reshape(-1,3);f=np.asarray(shape.geometry.faces).reshape(-1,3);mesh=trimesh.Trimesh(vertices=v,faces=f,process=False);cut=trimesh.intersections.mesh_plane(mesh,frame[:3,0],origin);assert len(cut)>0
  xy=np.stack([(cut-origin)@frame[:3,2],(cut-origin)@frame[:3,1]],axis=-1);segments.append((obj.GlobalId,xy));counts[obj.GlobalId]=0
 allpts=np.concatenate([s.reshape(-1,2) for _,s in segments]);cellx=.15+(index%3)*1.9;celly=3.05-(index//3)*1.;offset=np.array([cellx-allpts[:,0].min(),celly])
 for guid,items in segments:
  for seg in items:
   if np.linalg.norm(seg[1]-seg[0])<1e-10:continue
   e=ms.add_line(tuple(seg[0]+offset),tuple(seg[1]+offset),dxfattribs={'layer':'NATIVE_SIDE_CUT'});e.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
 geo=calculate(trans,'start','end');assert np.allclose(geo['inlet_section_m'],r['new_section_m'],atol=1e-10,rtol=0) and np.allclose(geo['outlet_section_m'],r['old_section_m'],atol=1e-10,rtol=0)
 node=flows['cases']['maximum']['port_flows'][r['branch_port_guid']]['source_node'];a,b=geo['inlet_section_m'],geo['outlet_section_m'];label=f'{node}: {a[0]*1000:.0f}x{a[1]*1000:.0f} to {b[0]*1000:.0f}x{b[1]*1000:.0f}mm';ms.add_text(label,dxfattribs={'height':.033,'insert':(cellx,celly+.34),'layer':'DETAIL_NOTES'});ms.add_text('Original branch endpoint retained',dxfattribs={'height':.028,'insert':(cellx,celly-.34),'layer':'DETAIL_NOTES'});labels.append(label)
assert len(counts)==18 and all(counts.values())
for text,y,height in [('CONSTANT HEIGHT BRANCH DETAILS',3.84,.07),('Actual saved native side cuts | 1:20 | not installed elevation',3.64,.045),('Gauge, collar and nominal/internal assumptions retained; local losses remain conditional',.38,.035),('Short adjacent fitting interaction, products, full pressure and installed clearance unresolved',.20,.035)]:ms.add_text(text,dxfattribs={'height':height,'insert':(.15,y),'layer':'DETAIL_NOTES'})
ref=ms.add_line((.15,.55),(.65,.55),dxfattribs={'layer':'DETAIL_REFERENCE'});ref.set_xdata('BSA_IFC',[(1000,cases[0]['tee_guid'])]);ms.add_text('0.5m reference',dxfattribs={'height':.035,'insert':(.75,.53),'layer':'DETAIL_NOTES'})
p=O/'Constant Height Branch Details.dxf';d.saveas(p);sheet=dict(source='Native saved145body model side sections of9tee/contraction assemblies',window_drawing_units=[0,0,5.8,4.],scale_denominator=20,reference_ifc_guid=cases[0]['tee_guid'],reference_layer='DETAIL_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),native_product_section_counts=counts,represented_products=18,assembly_count=9,labels=labels,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('9native side details saved/reopened')
