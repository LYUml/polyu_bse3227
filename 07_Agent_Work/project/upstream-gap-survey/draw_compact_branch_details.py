from pathlib import Path
import json,hashlib
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh,ezdxf
from ifcopenshell.util.placement import get_local_placement
from bsa.ifc_native import run
from bsa.duct_transition_quantities import calculate
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/compact-branch-stages');O=R/'details';O.mkdir(exist_ok=False);source=R/'Supply Network.ifc';m=ifcopenshell.open(str(source));cases=json.loads((R/'integration.json').read_text())['cases'];flow=json.loads((R/'flow-review.json').read_text());settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');ms=doc.modelspace()
for name in ['BSA_DETAIL_CUT','BSA_DETAIL_NOTES','BSA_SECTION_REFERENCE']:doc.layers.new(name)
counts={};labels=[]
for index,r in enumerate(cases):
 tee=m.by_guid(r['tee_guid']);frame=get_local_placement(m.by_guid(r['branch_port_guid']).ObjectPlacement);origin=get_local_placement(tee.ObjectPlacement)[:3,3];objects=[tee]+[m.by_guid(g) for g in r['transition_guids']];node=flow['cases']['maximum']['port_flows'][r['branch_port_guid']]['source_node']
 native=[calculate(objects[i],'start','end') for i in [1,2]];assert np.allclose(native[0]['inlet_section_m'],r['new_section_m'],atol=1e-10,rtol=0) and np.allclose(native[1]['outlet_section_m'],r['old_section_m'],atol=1e-10,rtol=0)
 for column,view in enumerate(['SIDE','PLAN']):
  normal=frame[:3,0 if view=='SIDE' else 1];vertical=frame[:3,1 if view=='SIDE' else 0];segments=[]
  for obj in objects:
   shape=ifcopenshell.geom.create_shape(settings,obj);v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3);mesh=trimesh.Trimesh(vertices=v,faces=f,process=False);cut=trimesh.intersections.mesh_plane(mesh,normal,origin);assert len(cut)>0;xy=np.stack([(cut-origin)@frame[:3,2],(cut-origin)@vertical],axis=-1);segments.append((obj.GlobalId,xy));counts.setdefault(obj.GlobalId,0)
  pts=np.concatenate([seg.reshape(-1,2) for _,seg in segments]);left=.15+2.9*column;cy=2.9-index*1.55;offset=np.array([left-pts[:,0].min(),cy])
  for guid,segs in segments:
   for seg in segs:
    if np.linalg.norm(seg[1]-seg[0])<1e-10:continue
    e=ms.add_line(tuple(seg[0]+offset),tuple(seg[1]+offset),dxfattribs={'layer':'BSA_DETAIL_CUT'});e.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
  label=f'{node} / {view}: 440x{r["new_section_m"][1]*1000:.0f} >450x{r["new_section_m"][1]*1000:.0f} >450x250mm';ms.add_text(label,dxfattribs={'height':.033,'insert':(left,cy+pts[:,1].max()+.12),'layer':'BSA_DETAIL_NOTES'});labels.append(label)
  ms.add_text(f'Core stub {r["core_straight_beyond_main_outside_m"]*1000:.1f}mm; external endpoint retained',dxfattribs={'height':.03,'insert':(left,cy+pts[:,1].min()-.15),'layer':'BSA_DETAIL_NOTES'})
assert len(counts)==6 and len(labels)==4
for text,y,h in [('COMPACT BRANCH TRANSITION DETAILS',3.84,.07),('Actual native plan/side cuts | 1:20 | two45degree one-plane stages',3.64,.043),('440mm throat and minimum50mmcorestub are opt-in design targets,not product limits',.35,.035),('Gauge, joints, products, noise, close coupling and full pressure remain unverified',.18,.035)]:ms.add_text(text,dxfattribs={'height':h,'insert':(.15,y),'layer':'BSA_DETAIL_NOTES'})
e=ms.add_line((.15,.58),(.65,.58),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,cases[0]['tee_guid'])]);ms.add_text('0.5m reference',dxfattribs={'height':.035,'insert':(.75,.56),'layer':'BSA_DETAIL_NOTES'})
p=O/'Compact Branch Details.dxf';doc.saveas(p);sheet=dict(source='Actual149body native model,selected2tee/4transition bodies inplan/side',window_drawing_units=[0,0,5.8,4.],scale_denominator=20,reference_ifc_guid=cases[0]['tee_guid'],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),represented_products=6,native_product_section_counts=counts,assembly_count=2,views=4,labels=labels,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('2assemblies in4native views saved/reopened')
