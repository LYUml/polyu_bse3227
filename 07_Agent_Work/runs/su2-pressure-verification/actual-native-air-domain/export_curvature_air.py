import gmsh,json
from pathlib import Path
p=Path(__file__).parent;gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(p/'curvature-wall-only-layers.msh'));src=json.loads((p/'boundary-review.json').read_text());vols=gmsh.model.getEntities(3);surfs=gmsh.model.getBoundary(vols,combined=True,oriented=False);buckets={x['marker']:[] for x in src['caps']};walls=[]
for _,tag in surfs:
 _,coords,_=gmsh.model.mesh.getNodes(2,tag,includeBoundary=True);points=[coords[i:i+3] for i in range(0,len(coords),3)];hits=[x for x in src['caps'] if points and max(abs(sum((a-b)*n for a,b,n in zip(q,x['origin_m'],x['outward_normal']))) for q in points)<1e-8]
 if len(hits)>1:raise ValueError('ambiguous source cap plane')
 if hits:buckets[hits[0]['marker']].append(tag)
 else:walls.append(tag)
ids,coords,_=gmsh.model.mesh.getNodes();xyz={int(t):coords[i*3:i*3+3] for i,t in enumerate(ids)};flipped=[]
for cap in src['caps']:
 tags=buckets[cap['marker']];assert len(tags)==5
 for tag in tags:
  signs=[];types,_,arrays=gmsh.model.mesh.getElements(2,tag)
  for typ,nodes in zip(types,arrays):
   count=gmsh.model.mesh.getElementProperties(typ)[3]
   for i in range(0,len(nodes),count):
    a,b,c=[xyz[int(t)] for t in nodes[i:i+3]];u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];signs.append(sum(x*y for x,y in zip(cross,cap['outward_normal'])))
  if all(x<0 for x in signs):gmsh.model.mesh.reverse([(2,tag)]);flipped.append(tag)
  elif not all(x>0 for x in signs):raise ValueError('mixed cap orientation')
 gmsh.model.addPhysicalGroup(2,tags,name=cap['marker'])
assert len(walls)==53;gmsh.model.addPhysicalGroup(2,walls,name='wall');gmsh.model.addPhysicalGroup(3,[t for _,t in vols],name='fluid');gmsh.write(str(p/'curvature-wall-only-air.su2'));(p/'curvature-cap-label-review.json').write_text(json.dumps({'cap_surfaces':buckets,'wall_surfaces':len(walls),'reversed_surfaces':flipped,'pressure_accepted':False},indent=2));print('refined mesh exported, cap surfaces reversed:',len(flipped));gmsh.finalize()
