from pathlib import Path
import os,json,subprocess,shutil
from bsa.openfoam_mesh_review import assess_check_mesh
b=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=b/'plenum-family-1-balanced-core-optimized';(c/'system').mkdir();shutil.copy2(b/'plenum-family-1-resolution-core-optimized/system/controlDict',c/'system/controlDict');e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (c/'gmshToFoam.log').open('x') as f:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'gmshToFoam.exe'),'-case',str(c),str(c/'air-exterior-gmsh22.msh')],env=e,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
with (c/'checkMesh.log').open('x') as f:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'checkMesh.exe'),'-case',str(c),'-allTopology','-allGeometry'],env=e,stdout=f,stderr=subprocess.STDOUT)
a=assess_check_mesh((c/'checkMesh.log').read_text(),r.returncode);(c/'native-mesh-review.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a));print((c/'checkMesh.log').read_text()[-2000:])
