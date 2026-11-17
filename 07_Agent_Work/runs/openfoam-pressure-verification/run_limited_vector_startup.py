from pathlib import Path
import shutil,json,hashlib,os,subprocess
b=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');s=b/'actual-family-1-resolution-limited-gradient';c=b/'actual-family-1-resolution-limited-vector';c.mkdir()
for d in ['constant','system']:shutil.copytree(s/d,c/d)
(c/'0').mkdir();h={}
for n in ['U','p','k','omega','nut']:
 shutil.copy2(s/'0'/n,c/'0'/n);h[n]=hashlib.sha256((c/'0'/n).read_bytes()).hexdigest()
p=c/'system/fvSchemes';t=p.read_text();old='bounded Gauss linearUpwind grad(U)';assert t.count(old)==1;p.write_text(t.replace(old,'bounded Gauss limitedLinearV 1'))
(c/'system/controlDict').write_text('FoamFile {format ascii;class dictionary;object controlDict;}\napplication foamRun;solver incompressibleFluid;startFrom startTime;startTime 0;stopAt endTime;endTime 20;deltaT 1;writeControl timeStep;writeInterval 20;writeFormat ascii;writePrecision 17;runTimeModifiable false;\n')
(c/'limited-vector-inputs.json').write_text(json.dumps({'scope':'Controlled velocity-convection startup screen only','source_initial_case':s.name,'initial_field_sha256':h,'only_active_method_change':'U convection boundedGausslimitedLinearV1; cellLimitedgrad(U), turbulenceupwind and relaxation remain unchanged','upstream':'https://doc.cfd.direct/openfoam/user-guide-v12/fvschemes','engineering_accepted':False},indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (c/'foamRun-startup20.log').open('x') as f:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(c)],env=e,stdout=f,stderr=subprocess.STDOUT)
print('native_returncode',r.returncode)
