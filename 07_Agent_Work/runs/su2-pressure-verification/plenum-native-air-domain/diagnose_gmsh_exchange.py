import gmsh,hashlib,json
from pathlib import Path
p=Path(__file__).parent/'family-1-layers'
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
results=[]
try:
 for name in ('air-planar-caps.msh','air-exterior-gmsh22.msh'):
  gmsh.clear();gmsh.open(str(p/name));ts,ids,arrays=gmsh.model.mesh.getElements(3);counts={};h=hashlib.sha256();tags=[];used=set()
  for t,ids,a in sorted(zip(ts,ids,arrays),key=lambda x:int(x[0])):
   n=gmsh.model.mesh.getElementProperties(t)[3];counts[int(t)]=len(ids);tags.extend(int(x) for x in ids)
   records=sorted(tuple(int(x) for x in a[i:i+n]) for i in range(0,len(a),n))
   for row in records:h.update((str(int(t))+':'+','.join(map(str,row))+'\n').encode());used.update(row)
  nt,xyz,_=gmsh.model.mesh.getNodes();points={int(k):tuple(float(x) for x in xyz[i*3:i*3+3]) for i,k in enumerate(nt) if int(k) in used};r=dict(file=name,volume_counts=counts,connectivity_without_element_ids_sha256=h.hexdigest(),minimum_element_id=min(tags),maximum_element_id=max(tags),used_nodes=len(used),min_node=min(used),max_node=max(used));results.append((r,points))
 assert set(results[0][1])==set(results[1][1]);maxdelta=max(sum((a-b)**2 for a,b in zip(results[0][1][k],results[1][1][k]))**.5 for k in results[0][1]);out=dict(files=[r for r,_ in results],maximum_coordinate_difference_m=maxdelta)
 (p/'gmsh22-identity-diagnostic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
finally:gmsh.finalize()
