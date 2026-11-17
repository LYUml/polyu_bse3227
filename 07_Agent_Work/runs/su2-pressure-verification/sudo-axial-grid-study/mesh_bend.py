from pathlib import Path
import gmsh,json,hashlib
p=Path(__file__).parent
gmsh.initialize()
try:
 gmsh.option.setNumber('General.Terminal',0)
 gmsh.open(str(p/'bend.geo'))
 gmsh.model.mesh.generate(3)
 types,tags,nodes=gmsh.model.mesh.getElements(3)
 counts={int(t):len(v) for t,v in zip(types,tags)}
 assert set(counts)=={5},counts
 element_tags=[int(x) for v in tags for x in v]
 quality=gmsh.model.mesh.getElementQualities(element_tags,'minSICN')
 volumes=gmsh.model.mesh.getElementQualities(element_tags,'volume')
 assert min(quality)>0 and min(volumes)>0
 gmsh.write(str(p/'bend.msh'))
 gmsh.write(str(p/'bend.su2'))
 result=dict(elements_by_gmsh_type=counts,minimum_SICN=float(min(quality)),minimum_signed_volume_m3=float(min(volumes)),total_cell_volume_m3=float(sum(volumes)),mesh_sha256=hashlib.sha256((p/'bend.su2').read_bytes()).hexdigest(),engineering_accepted=False,scope='Native Gmsh generation and cell quality only; boundary geometry/flow/source validation pending.')
 with (p/'mesh-review.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
finally:gmsh.finalize()
