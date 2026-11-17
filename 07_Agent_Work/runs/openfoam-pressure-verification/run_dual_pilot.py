from pathlib import Path
import os,json,subprocess,hashlib
from bsa.openfoam_mesh_review import assess_check_mesh
b=Path(__file__).parent;c=b/'plenum-family-1-local-dual-pilot'
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text(encoding='utf-8')));e['OMP_NUM_THREADS']='1'
with (c/'polyDualMesh.log').open('x',encoding='utf-8') as log:
 r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'polyDualMesh.exe'),'-case',str(c),'-concaveMultiCells','-overwrite','60'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=120)
print('polyDualMesh',r.returncode,flush=True)
assert r.returncode==0
with (c/'checkMesh.log').open('x',encoding='utf-8') as log:
 r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'checkMesh.exe'),'-case',str(c),'-allTopology','-allGeometry'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=120)
review=assess_check_mesh((c/'checkMesh.log').read_text(encoding='utf-8'),r.returncode)
inputs=json.loads((c/'pilot-inputs.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((b/inputs['source_case']/'constant/polyMesh'/n).read_bytes()).hexdigest()==v for n,v in inputs['source_mesh_sha256'].items())
review['original_source_mesh_unchanged']=True
(c/'native-mesh-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps(review),flush=True);print((c/'checkMesh.log').read_text(encoding='utf-8')[-1700:],flush=True)
