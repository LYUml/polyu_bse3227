from pathlib import Path
import os,json,subprocess
from bsa.openfoam_mesh_review import assess_check_mesh
c=Path(__file__).parent/'plenum-family-1-local-uniform-hex-trial'
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text(encoding='utf-8')));e['OMP_NUM_THREADS']='1'
results={}
for exe,args in [('blockMesh',[]),('snappyHexMesh',['-overwrite']),('checkMesh',['-allTopology','-allGeometry'])]:
 with (c/(exe+'.log')).open('x',encoding='utf-8') as log:
  r=subprocess.run([str(Path(e['FOAM_APPBIN'])/(exe+'.exe')),'-case',str(c),*args],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 results[exe]=r.returncode
 print(exe,r.returncode,flush=True)
 if exe!='checkMesh':assert r.returncode==0
review=assess_check_mesh((c/'checkMesh.log').read_text(encoding='utf-8'),results['checkMesh'])
review['native_returncodes']=results
review['scope']='Coarse no-layer hex-dominant mesh feasibility; geometry/wall resolution/pressure not accepted'
(c/'native-mesh-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps(review),flush=True)
print((c/'checkMesh.log').read_text(encoding='utf-8')[-1800:],flush=True)
