from pathlib import Path
import json,hashlib
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh,ezdxf
from ifcopenshell.util.placement import get_local_placement
from bsa.ifc_native import run
from bsa.duct_transition_quantities import calculate
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/supported-transition-stages');O=R/'details';O.mkdir(exist_ok=False);source=R/'Supply Network.ifc';m=ifcopenshell.open(str(source));cases=json.loads((R/'integration.json').read_text())['cases'];flows=json.loads((R/'flow-review.json').read_text());settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');ms=doc.modelspace()
for name in ['BSA_DETAIL_CUT','BSA_DETAIL_NOTES','BSA_SECTION_REFERENCE']:doc.layers.new(name)
counts={};labels=[]
for index,r in enumerate(cases):
 objects=[m.by_guid(r['original_guid']),m.by_guid(r['second_guid'])];frame=np.array(r['frame']);origin=frame[:3,3];segments=[]
 for obj in objects:
  shape=ifcopenshell.geom.create_shape(settings,obj);v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3);cut=trimesh.intersections.mesh_plane(trimesh.Trimesh(vertices=v,faces=f,process=False),frame[:3,0],origin);assert len(cut)>0;xy=np.stack([(cut-origin)@frame[:3,2],(cut-origin)@frame[:3,1]],axis=-1);segments.append((obj.GlobalId,xy));counts[obj.GlobalId]=0
 pts=np.concatenate([seg.reshape(-1,2) for _,seg in segments]);left=.18+(index%3)*2.4;cy=3.95-(index//3)*1.3;offset=np.array([left-pts[:,0].min(),cy])
 for guid,segs in segments:
  for seg in segs:
   if np.linalg.norm(seg[1]-seg[0])<1e-10:continue
   e=ms.add_line(tuple(seg[0]+offset),tuple(seg[1]+offset),dxfattribs={'layer':'BSA_DETAIL_CUT'});e.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
 for obj in objects:calculate(obj,'start','end')
 binding=flows['cases']['maximum']['port_flows'][r['inlet_guid']];sizes=' > '.join(f'{v[0]*1000:.0f}x{v[1]*1000:.0f}' for v in [r['start_section_m'],r['intermediate_section_m'],r['end_section_m']]);label=binding['source_node']+' '+binding['source_section']+': '+sizes+'mm';labels.append(label);ms.add_text(label,dxfattribs={'height':.034,'insert':(left,cy+pts[:,1].max()+.11),'layer':'BSA_DETAIL_NOTES'});ms.add_text(f'45deg stages; straight change {-r["additional_length_m"]*1000:+.1f}mm',dxfattribs={'height':.03,'insert':(left,cy+pts[:,1].min()-.14),'layer':'BSA_DETAIL_NOTES'})
assert len(counts)==18 and all(counts.values())
for text,y,h in [('SOURCE FAMILY TRANSITION DETAILS',4.80,.085),('Actual native side cuts | 1:25 | one-plane then equal-angle pyramidal contraction',4.57,.05),('45degreeangles,50mmcollars and0.8mmoffset remain study assumptions',.24,.04),('Tentative source data, friction/stations, short-fitting interaction and products remain unverified',.08,.037)]:ms.add_text(text,dxfattribs={'height':h,'insert':(.18,y),'layer':'BSA_DETAIL_NOTES'})
e=ms.add_line((.18,.48),(.68,.48),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,cases[0]['original_guid'])]);ms.add_text('0.5m reference',dxfattribs={'height':.04,'insert':(.78,.46),'layer':'BSA_DETAIL_NOTES'})
p=O/'Source Family Transition Details.dxf';doc.saveas(p);sheet=dict(source='Actual158body native model,18transition bodies in9sideviews',window_drawing_units=[0,0,7.25,5.],scale_denominator=25,reference_ifc_guid=cases[0]['original_guid'],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),represented_products=18,native_product_section_counts=counts,assembly_count=9,views=9,labels=labels,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('9actual stage side details saved/reopened')
