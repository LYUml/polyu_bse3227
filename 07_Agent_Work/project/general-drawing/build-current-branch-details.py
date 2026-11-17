from pathlib import Path
import json,hashlib
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh
from ifcopenshell.util.placement import get_local_placement
from bsa.circular_geometry import configure
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');R=B/'runs/recentered-constant-height-network';S=R/'Supply Network.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sourcehash=sha(S)
assert sourcehash==json.loads((R/'native-cap-review.json').read_text())['ifc_sha256']
cases=json.loads((R/'integration.json').read_text())['cases'];model=ifcopenshell.open(str(S));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);configure(settings);views=[];rows=[]
for i,c in enumerate(cases):
 cfg=json.loads((R/(c['folder']+'.json')).read_text());frame=np.eye(4);frame[:3,:3]=cfg['placement']['rotation'];frame[:3,3]=cfg['placement']['origin_m'];origin=frame[:3,3];axis=frame[:3,2];vertical=frame[:3,1];normal=frame[:3,0];entities=[];allpts=[];counts={}
 source=f'Saved IFC SHA256 {sourcehash}; branch assembly {c["tee_guid"]} / {c["transition_guid"]}'
 def entity(id,kind,layer,**kw):return dict(id=f'branch-{i+1}:{id}',kind=kind,layer=layer,source=source,classification='secondary_transcription',**kw)
 for guid in [c['tee_guid'],c['transition_guid']]:
  shape=ifcopenshell.geom.create_shape(settings,model.by_guid(guid));v=np.asarray(shape.geometry.verts).reshape(-1,3);f=np.asarray(shape.geometry.faces).reshape(-1,3);cut=trimesh.intersections.mesh_plane(trimesh.Trimesh(vertices=v,faces=f,process=False),normal,origin);assert len(cut)>0;xy=np.stack([(cut-origin)@axis,(cut-origin)@vertical],axis=-1)*1000;counts[guid]=0
  for j,seg in enumerate(xy):
   if np.linalg.norm(seg[1]-seg[0])<1e-7:continue
   entities.append(entity(f'{guid}:{j}','line','MATERIAL',start=seg[0].tolist(),end=seg[1].tolist()));counts[guid]+=1;allpts.extend(seg.tolist())
 pts=np.array(allpts);lo=pts.min(axis=0);hi=pts.max(axis=0)
 inlet=get_local_placement(model.by_guid(c['transition_inlet_guid']).ObjectPlacement)[:3,3];outlet=get_local_placement(model.by_guid(c['transition_outlet_guid']).ObjectPlacement)[:3,3];delta=outlet-inlet;length=float(delta@axis)*1000
 assert abs(length-c['transition_reach_m']*1000)<1e-7 and np.linalg.norm(delta-axis*(delta@axis))<1e-9
 dimy=float(lo[1]-25);a=float((inlet-origin)@axis)*1000;b=float((outlet-origin)@axis)*1000
 entities.append(entity('reach-dimension','dimension','ANNOTATION',p1=[a,dimy],p2=[b,dimy],distance=-45,text_height=12.5))
 sizes=' > '.join(f'{x[0]*1000:.0f}x{x[1]*1000:.0f}' for x in [c['new_section_m'],c['old_section_m']])
 labels=[(f'BRANCH {i+1}: {sizes} mm',float(hi[1]+50)),('Native side cut; transition length dimension in mm',float(hi[1]+25)),('30deg / 50mm collars / 0.8mm offset assumed',float(lo[1]-125)),('Loss correlation and product approval remain conditional',float(lo[1]-150))]
 for j,(text,y) in enumerate(labels):entities.append(entity(f'note-{j}','text','NOTES',insert=[float(lo[0]),y],text=text,height=12.5,rotation=0))
 views.append(dict(id=f'branch-{i+1}',entities=entities));rows.append(dict(case=i+1,source_guids=list(counts),native_segment_counts=counts,actual_transition_port_distance_mm=float(np.linalg.norm(delta))*1000,projected_dimension_mm=length))
spec=dict(schema='bsa.drawing-layout/1',source=f'Actual saved110body candidate branch side cuts; SHA256 {sourcehash}',units='mm',layers={k:dict(color=7,lineweight=18) for k in ['MATERIAL','ANNOTATION','NOTES']},blocks={},sheet=dict(paper='A1',window=[0,0,4135,2870],scale=5,title='CONSTANT HEIGHT BRANCH DETAILS',number='BSE3227-CS-02',reference_length=500),content_window=[50,150,4085,2750],gap_mm=8,views=views)
assert sha(S)==sourcehash and len(rows)==10
(B/'project/general-drawing/current-branch-details.json').write_text(json.dumps(spec,indent=2)+'\n')
(B/'project/general-drawing/current-branch-section-review.json').write_text(json.dumps(dict(ifc_sha256=sourcehash,assemblies=rows,views=10,represented_products=20,dimension_basis='Saved native transition port separation, checked against assembly record; nominal design model, not measured installation',design_accepted=False),indent=2))
print('10 actual native branch sections prepared')


