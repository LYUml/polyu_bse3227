from pathlib import Path
import os,json,subprocess
c=Path(__file__).parent/'plenum-family-1-local-feature-fine-hex'
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text(encoding='utf-8')));e['OMP_NUM_THREADS']='1'
with (c/'checkMesh-localized.log').open('x',encoding='utf-8') as log:
 r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'checkMesh.exe'),'-case',str(c),'-allTopology','-allGeometry','-writeSets','-writeSurfaces'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=120)
print('localized_native_returncode',r.returncode,flush=True)
assert r.returncode==0
assert (c/'constant/polyMesh/sets/concaveCells').exists()
