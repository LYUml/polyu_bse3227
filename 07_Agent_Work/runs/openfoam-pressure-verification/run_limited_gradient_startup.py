from pathlib import Path
import shutil,json,hashlib,os,subprocess
b=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');s=b/'actual-family-1-resolution-mixed-order';c=b/'actual-family-1-resolution-limited-gradient';c.mkdir()
for d in ['constant','system']:shutil.copytree(s/d,c/d)
(c/'0').mkdir();hashes={}
for n in ['U','p','k','omega','nut']:
 shutil.copy2(s/'0'/n,c/'0'/n);hashes[n]=hashlib.sha256((c/'0'/n).read_bytes()).hexdigest()
p=c/'system/fvSchemes';t=p.read_text();old='default         Gauss linear;';assert t.count(old)==1;t=t.replace(old,old+'\n    grad(U)         cellLimited Gauss linear 1;');p.write_text(t)
(c/'system/controlDict').write_text('FoamFile {format ascii;class dictionary;object controlDict;}\napplication foamRun;solver incompressibleFluid;startFrom startTime;startTime 0;stopAt endTime;endTime 20;deltaT 1;writeControl timeStep;writeInterval 20;writeFormat ascii;writePrecision 17;runTimeModifiable false;\n')
r={'scope':'Controlled 20-step native startup screen, not design pressure','source_initial_case':s.name,'initial_field_sha256':hashes,'only_numerical_method_change_from_mixed':'grad(U) cellLimited Gauss linear 1; velocity linearUpwind and turbulence upwind unchanged','source':'https://doc.cfd.direct/openfoam/user-guide-v12/fvschemes','engineering_accepted':False}
(c/'limited-gradient-inputs.json').write_text(json.dumps(r,indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (c/'foamRun-startup20.log').open('x') as log:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(c)],env=e,stdout=log,stderr=subprocess.STDOUT)
print('native_returncode',r.returncode)
