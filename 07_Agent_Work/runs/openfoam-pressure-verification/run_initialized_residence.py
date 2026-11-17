from pathlib import Path
import json,shutil,hashlib,os,subprocess,time
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs/openfoam-pressure-verification';s=B/'plenum-family-1-potential-outlet-reference';o=B/'plenum-family-1-initialized-residence';o.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(s)):sha(p) for f in ('constant','system','0.005') for p in (s/f).rglob('*') if p.is_file()}
for f in ('constant','system','0.005'):shutil.copytree(s/f,o/f)
p=o/'system/controlDict';t=p.read_text().replace('startTime 0;','startTime 0.005;').replace('endTime 0.005;','endTime 0.25;').replace('writeInterval 20;','writeInterval 200;');p.write_text(t)
f=(B/'actual-family-1-resolution-limited-vector/system/functions').read_text()
for n in ('inlet','outlet_0','outlet_1','outlet_2','outlet_3'):f=f.replace('name '+n+';','name air_'+n+';')
f+='wall_yPlus {type yPlus;libs ("libfieldFunctionObjects.dll");executeControl timeStep;writeControl timeStep;writeInterval 20;}\n'
(o/'system/functions').write_text(f)
policy={'scope':'Existing initialized saved state continuation to about one nominal residence time; not stationary pressure acceptance','start_s':.005,'end_s':.25,'deltaT_s':.00025,'additional_steps':980,'reference_residence_s':.24375340232499723,'runtime_cap_s':2400,'source_inputs_sha256':pins,'observer_pressure':'native total pressure, rho1.2 assumption, phi-weighted patch average','observer_source':'https://cpp.openfoam.org/v12/surfaceFieldValueTemplates_8C_source.html','pressure_adopted':False,'course_baseline_changed':False}
(o/'residence-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1';start=time.monotonic()
with (o/'foamRun.log').open('x') as log:
 try:
  r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(o),'-solver','incompressibleFluid'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=2400);rc=r.returncode
 except subprocess.TimeoutExpired:rc='runtime_cap_exceeded'
assert all(sha(s/p)==h for p,h in pins.items())
review={'returncode':rc,'elapsed_s':time.monotonic()-start,'source_inputs_preserved':True,'final_U_exists':(o/'0.25/U').exists(),'pressure_adopted':False};(o/'native-run-review.json').write_text(json.dumps(review,indent=2));print(json.dumps(review),flush=True)
