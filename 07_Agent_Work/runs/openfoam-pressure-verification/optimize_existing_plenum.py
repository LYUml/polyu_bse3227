from pathlib import Path
import gmsh,json,hashlib
base=Path(__file__).parent
src=base.parent/'su2-pressure-verification/plenum-native-air-domain/family-1-layers/air-exterior-gmsh22.msh'
out=base/'plenum-family-1-core-optimization';out.mkdir(exist_ok=False)
gmsh.initialize();gmsh.option.setNumber('General.Terminal',1);gmsh.open(str(src))
def coords():
 t,a,_=gmsh.model.mesh.getNodes();return {int(v):tuple(float(x) for x in a[i*3:i*3+3]) for i,v in enumerate(t)}
def elements(dim):
 ts,es,ns=gmsh.model.mesh.getElements(dim);return [(int(t),[int(x) for x in e],[int(x) for x in n]) for t,e,n in zip(ts,es,ns)]
before=coords();vol=elements(3);sur=elements(2);protected=set()
for typ,tags,nodes in vol:
 if typ==6:protected.update(nodes)
for typ,tags,nodes in sur:protected.update(nodes)
gmsh.model.mesh.optimize('',force=True,niter=5)
after=coords();changed=[i for i in before if before[i]!=after[i]]
r={'method':'Gmsh4.15.2 default tetrahedral optimizer forceTrue niter5','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'moved_nodes':len(changed),'moved_protected_nodes':len(set(changed)&protected),'volume_connectivity_unchanged':elements(3)==vol,'surface_connectivity_unchanged':elements(2)==sur,'engineering_accepted':False}
(out/'optimization-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
if set(changed)&protected:raise RuntimeError('Protected boundary/prism nodes moved; candidate rejected')
assert elements(2)==sur
assert all(x>0 for x in gmsh.model.mesh.getElementQualities([v for _,tags,_ in elements(3) for v in tags],'minDetJac'))
gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.Renumber',0);gmsh.write(str(out/'air-exterior-gmsh22.msh'));gmsh.finalize()
