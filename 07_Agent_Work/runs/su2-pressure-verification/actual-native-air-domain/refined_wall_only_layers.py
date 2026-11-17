import gmsh,json
from pathlib import Path
p=Path(__file__).parent;gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4);gmsh.model.add('wall-only-layers');v=gmsh.model.occ.importShapes(str(p/'actual-air.brep'));gmsh.model.occ.synchronize();src=json.loads((p/'boundary-review.json').read_text());caps={x['surface_tag'] for x in src['caps']};surfs=gmsh.model.getBoundary(v,oriented=False);walls=[s for s in surfs if s[1] not in caps];gmsh.model.occ.remove(v,recursive=False);gmsh.model.occ.remove([(2,t) for t in caps],recursive=False);gmsh.model.occ.synchronize();gmsh.option.setNumber('Mesh.MeshSizeMax',.10);gmsh.option.setNumber('Mesh.MeshSizeMin',.025)
heights=[];h=0
for i in range(22):h+=.00001*1.3**i;heights.append(-h)
try:
 ex=gmsh.model.geo.extrudeBoundaryLayer(walls,[1]*22,heights,True);gmsh.model.geo.synchronize();top=[ex[i-1] for i in range(1,len(ex)) if ex[i][0]==3];curves=gmsh.model.getBoundary(top,combined=True,oriented=False);ends={t:{x[1] for x in gmsh.model.getBoundary([(1,t)],oriented=False)} for _,t in curves};todo=set(ends);groups=[]
 while todo:
  group={todo.pop()};points=set(ends[next(iter(group))]);changed=True
  while changed:
   adjacent={t for t in todo if points&ends[t]};changed=bool(adjacent)
   for t in adjacent:points|=ends[t]
   group|=adjacent;todo-=adjacent
  groups.append(sorted(group))
 if len(groups)!=5:raise ValueError(('cap loops',len(groups)))
 newcaps=[gmsh.model.geo.addPlaneSurface([gmsh.model.geo.addCurveLoop(g,reorient=True)]) for g in groups];sl=gmsh.model.geo.addSurfaceLoop([t for _,t in top]+newcaps);gmsh.model.geo.addVolume([sl]);gmsh.model.geo.synchronize();gmsh.model.mesh.generate(3);gmsh.write(str(p/'refined-wall-only-layers.msh'));print('success',len(gmsh.model.mesh.getNodes()[0]))
except Exception as e:
 (p/'refined-wall-only-error.txt').write_text(str(e));print(type(e).__name__,str(e))
finally:gmsh.finalize()
