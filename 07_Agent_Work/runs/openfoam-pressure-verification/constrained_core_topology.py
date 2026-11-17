from pathlib import Path
from collections import Counter
import gmsh,json,hashlib
base=Path(__file__).parent
src=base.parent/'su2-pressure-verification/plenum-native-air-domain/family-1-layers/air-exterior-gmsh22.msh'
out=base/'plenum-family-1-constrained-core-topology';out.mkdir(exist_ok=False)
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('Mesh.Renumber',0);gmsh.open(str(src));original=gmsh.model.getCurrent()
def coords():
 t,a,_=gmsh.model.mesh.getNodes();return {int(v):tuple(float(x) for x in a[i*3:i*3+3]) for i,v in enumerate(t)}
def elements(dim):
 ts,es,ns=gmsh.model.mesh.getElements(dim);return [(int(t),[int(x) for x in e],[int(x) for x in n]) for t,e,n in zip(ts,es,ns)]
before=coords();vol=elements(3);sur=elements(2);protected=set()
for typ,tags,nodes in vol:
 if typ==6:protected.update(nodes)
for typ,tags,nodes in sur:protected.update(nodes)
tets=next(x for x in vol if x[0]==4);tags=tets[1];flat=tets[2];used=set(flat);faces={};inc=Counter()
for i in range(0,len(flat),4):
 a,b,c,d=flat[i:i+4]
 for face in ((a,c,b),(a,b,d),(b,c,d),(c,a,d)):
  key=tuple(sorted(face));inc[key]+=1;faces[key]=face
assert max(inc.values())==2
boundary=[faces[k] for k,n in inc.items() if n==1];boundary_nodes={i for face in boundary for i in face}
assert used&protected<=boundary_nodes
print('core',len(tags),'boundary triangles',len(boundary),flush=True)
gmsh.model.add('tet_core');gmsh.model.addDiscreteEntity(2,1);gmsh.model.addDiscreteEntity(3,1,[1]);nodes=sorted(used)
gmsh.model.mesh.addNodes(3,1,nodes,[x for i in nodes for x in before[i]])
gmsh.model.mesh.addElementsByType(1,2,list(range(max(tags)+1,max(tags)+1+len(boundary))),[x for face in boundary for x in face])
gmsh.model.mesh.addElementsByType(1,4,tags,flat);gmsh.model.mesh.reclassifyNodes()
gmsh.option.setNumber('Mesh.OptimizeThreshold',0.8)
gmsh.model.mesh.optimize('',force=True,niter=5)
after=coords();changed=[i for i in used if before[i]!=after[i]]
assert not set(changed)&protected
assert not set(changed)&boundary_nodes
newtets=next(x for x in elements(3) if x[0]==4)
newinc=Counter()
for i in range(0,len(newtets[2]),4):
 a,b,c,d=newtets[2][i:i+4]
 for face in ((a,c,b),(a,b,d),(b,c,d),(c,a,d)):newinc[tuple(sorted(face))]+=1
assert max(newinc.values())==2
assert {k for k,n in newinc.items() if n==1}=={tuple(sorted(f)) for f in boundary}
assert min(gmsh.model.mesh.getElementQualities(newtets[1],'minDetJac'))>0
print('changed internal nodes',len(changed),flush=True)
gmsh.model.setCurrent(original)
for i in changed:gmsh.model.mesh.setNode(i,after[i],[])
entities=gmsh.model.getEntities(3)
assert len(entities)==1
gmsh.model.mesh.removeElements(3,entities[0][1],tags)
first=max(i for _,ts,_ in vol+sur for i in ts)+1
gmsh.model.mesh.addElementsByType(entities[0][1],4,list(range(first,first+len(newtets[1]))),newtets[2])
assert next(x for x in elements(3) if x[0]==6)==next(x for x in vol if x[0]==6)
assert elements(2)==sur
assert min(gmsh.model.mesh.getElementQualities([i for _,ts,_ in elements(3) for i in ts],'minDetJac'))>0
gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(out/'air-exterior-gmsh22.msh'))
r={'method':'Gmsh4.15.2 default tetrahedral optimizer five iterations threshold0.8 on extracted original tetrahedral core with explicit discrete triangular boundary','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'core_tetrahedra':len(tags),'core_boundary_triangles':len(boundary),'moved_nodes':len(changed),'moved_protected_nodes':0,'prism_connectivity_unchanged':True,'core_boundary_faces_unchanged':True,'optimized_core_tetrahedra':len(newtets[1]),'surface_connectivity_unchanged':True,'engineering_accepted':False}
(out/'optimization-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True);gmsh.finalize()
