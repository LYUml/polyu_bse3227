from pathlib import Path
import json,hashlib
import numpy as np
import ifcopenshell,ifcopenshell.geom,ifcopenshell.util.unit
from bsa.source_network_drawing import project
from bsa.circular_geometry import configure
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');R=B/'runs/recentered-constant-height-network';S=R/'Supply Network.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((R/'native-cap-review.json').read_text());assert sha(S)==receipt['ifc_sha256'];clash=json.loads((R/'raw-clash/clash.json').read_text());assert clash['valid_geometry_count']==110 and clash['intersection_pair_count']==0
model=ifcopenshell.open(str(S));assert ifcopenshell.util.unit.calculate_unit_scale(model)==1
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);configure(settings)
items=[];points=[]
for obj in sorted(model.by_type('IfcDistributionElement'),key=lambda o:o.GlobalId):
 shape=ifcopenshell.geom.create_shape(settings,obj);mesh=shape.geometry;v=np.asarray(mesh.verts).reshape(-1,3);f=np.asarray(mesh.faces).reshape(-1,3);items.append((obj.GlobalId,project(v,f)));points.append(v)
assert len(items)==110
v=np.vstack(points);lo=v[:,:2].min(axis=0);hi=v[:,:2].max(axis=0);span=hi-lo
scale=next(s for s in [150,200,250,300,400] if span[0]<=.265*s and span[1]<=.14*s);offset=np.array([.012*scale,.035*scale])-lo
entities=[];counts={}
for guid,polygons in items:
 counts[guid]=0
 for polygon in polygons:
  for ring in [polygon.exterior,*polygon.interiors]:
   vertices=(np.asarray(ring.coords)[:-1]+offset)*1000
   entities.append(dict(id=f'{guid}:outline:{counts[guid]}',kind='polyline',layer='MATERIAL',source=f'Saved IFC SHA256 {sha(S)}; product {guid}; native material XY silhouette',classification='secondary_transcription',points=vertices.tolist(),closed=True));counts[guid]+=1
for i,text in enumerate(['110 native bodies; 20 rigid outlet paths; source model in metres','XY material projection only; no architectural context or hidden-line removal','Conditional losses; complete pressure, products and installed clearances unverified']):
 entities.append(dict(id=f'note-{i}',kind='text',layer='NOTES',source='Host review scope; existing candidate limitations',classification='assumed',insert=[.012*scale*1000,(.181-i*.007)*scale*1000],text=text,height=.0024*scale*1000,rotation=0))
doc=dict(schema='bsa.drawing-document/1',source=f'Actual current constant-height candidate IFC SHA256 {sha(S)}; review drawing only',units='mm',layers={'MATERIAL':dict(color=7,lineweight=18),'NOTES':dict(color=7,lineweight=18)},blocks={},entities=entities,sheet=dict(paper='A4',window=[0,0,290*scale,200*scale],scale=scale,title='SUPPLY NETWORK COORDINATION STUDY',number='BSE3227-CS-01',reference_length=10000))
p=B/'project/general-drawing/current-network-plan.json';p.write_text(json.dumps(doc,indent=2)+'\n')
(B/'project/general-drawing/current-network-projection.json').write_text(json.dumps(dict(ifc_sha256=sha(S),component_contour_counts=counts,represented_products=110,translation_xy_m=offset.tolist(),scale=scale,projection_method='Existing source_network_drawing.project; native world-coordinate meshes; no model scaling',design_accepted=False),indent=2))
print(json.dumps(dict(products=len(counts),entities=len(entities),scale=scale,source_unchanged=sha(S)==receipt['ifc_sha256'])))

