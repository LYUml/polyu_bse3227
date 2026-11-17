from pathlib import Path
import gmsh,json,hashlib,shutil
b=Path(__file__).parent
source_mesh=b/'plenum-family-1-balanced-core-optimized/air-exterior-gmsh22.msh'
base=b/'plenum-family-1-local-feature-fine-hex'
c=b/'plenum-family-1-local-region-fine-hex'
c.mkdir(exist_ok=False);shutil.copytree(base/'system',c/'system');(c/'constant/triSurface').mkdir(parents=True)
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(source_mesh))
tags,flat,_=gmsh.model.mesh.getNodes();xyz={int(n):tuple(float(x) for x in flat[i*3:i*3+3]) for i,n in enumerate(tags)}
wall={}
for d,g in gmsh.model.getPhysicalGroups(2):
 if gmsh.model.getPhysicalName(d,g)!='wall':continue
 for entity in gmsh.model.getEntitiesForPhysicalGroup(d,g):
  types,ets,arrays=gmsh.model.mesh.getElements(2,int(entity))
  for kind,arr in zip(types,arrays):
   assert kind==2
   for j in range(0,len(arr),3):
    key=tuple(sorted(xyz[int(n)] for n in arr[j:j+3]));assert key not in wall;wall[key]=int(entity)
gmsh.finalize()
old=base/'constant/triSurface/air.obj';lines=old.read_text(encoding='utf-8').splitlines();vertices=[line for line in lines if line.startswith('v ')]
origin=[68.245932,18.590709,0.]
world=[tuple(float(s)+v for s,v in zip(line.split()[1:],origin)) for line in vertices]
rows=[];group=None;seen=set();counts={}
for line in lines:
 if line.startswith('g '):group=line.split()[1]
 elif line.startswith('f '):
  ids=[int(n)-1 for n in line.split()[1:]];assert len(ids)==3
  label=group
  if group=='wall':
   key=tuple(sorted(world[i] for i in ids));entity=wall[key];assert key not in seen;seen.add(key);label='wall_'+str(entity)
  rows.append((label,line));counts[label]=counts.get(label,0)+1
assert seen==set(wall) and len(wall)==25778
assert set(counts)-{k for k in counts if k.startswith('wall_')}=={'inlet','outlet_0','outlet_1','outlet_2','outlet_3'}
assert len([k for k in counts if k.startswith('wall_')])==9
out=c/'constant/triSurface/air.obj'
with out.open('x',encoding='utf-8',newline='\n') as f:
 for line in vertices:f.write(line+'\n')
 last=None
 for label,line in rows:
  if label!=last:f.write('g '+label+'\n');last=label
  f.write(line+'\n')
new=out.read_text(encoding='utf-8').splitlines()
assert [s for s in new if s.startswith('v ')]==vertices
assert [s for s in new if s.startswith('f ')]==[s for s in lines if s.startswith('f ')]
p=c/'system/snappyHexMeshDict';s=p.read_text(encoding='utf-8');assert 'snapControls {' in s;s=s.replace('snapControls {','snapControls {multiRegionFeatureSnap true;');p.write_text(s,encoding='utf-8')
p=c/'system/surfaceFeaturesDict';s=p.read_text(encoding='utf-8');assert 'geometricTestOnly' not in s;s+='\ngeometricTestOnly false;\n';p.write_text(s,encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'scope':'Restore existing Gmsh wall-entity regions for native mesh alignment; no geometry/face edit','source_gmsh_mesh_sha256':sha(source_mesh),'source_surface_sha256':sha(old),'regrouped_surface_sha256':sha(out),'vertices_preserved_byte_exact':True,'ordered_oriented_triangles_preserved_byte_exact':True,'all25778wall_triangles_bound_to_source_entities':True,'wall_regions':9,'port_regions_unchanged':5,'region_triangle_counts':counts,'feature_policy':'Same explicit150degree features plus source-region boundaries and multiRegionFeatureSnap; same fine mesh density and strict criteria','source_geometry_changed':False,'engineering_accepted':False}
(c/'source-regions-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
inputs=json.loads((base/'mesh-trial-inputs.json').read_text(encoding='utf-8'));inputs['source_surface_sha256']=sha(out);inputs['feature_policy']=r['feature_policy'];(c/'mesh-trial-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r,indent=2),flush=True)
