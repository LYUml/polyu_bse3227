from pathlib import Path
import json,shutil,hashlib,os,subprocess,time,sys
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');kind=sys.argv[1];assert kind in ('baseline','extended')
source_name,initial=('plenum-family-1-initialized-residence','0.25') if kind=='baseline' else ('plenum-family-1-extended-face-pressure-startup','0.255')
s=B/source_name;o=B/('plenum-family-1-boundary-comparison-'+kind);o.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(s)):sha(p) for f in ('constant','system',initial) for p in (s/f).rglob('*') if p.is_file()}
for f in ('constant','system',initial):shutil.copytree(s/f,o/f)
p=o/'system/controlDict';t=p.read_text();import re
t=re.sub(r'(?<![A-Za-z])startTime [^;]+;','startTime '+initial+';',t);t=re.sub(r'endTime [^;]+;','endTime 0.5;',t);t=re.sub(r'writeInterval [^;]+;','writeInterval 200;',t);p.write_text(t)
policy={'scope':'Paired outlet-domain sensitivity diagnostic; not validated fitting pressure','kind':kind,'source_case':source_name,'start_s':float(initial),'end_s':.5,'deltaT_s':.00025,'comparison_window_s':[.45,.5],'compare_original_stations':True,'new_extension_initialization_transient_retained':kind=='extended','time_mesh_physical_validation_accepted':False,'runtime_cap_s':2400,'source_sha256':pins,'pressure_adopted':False};(o/'comparison-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1';start=time.monotonic()
with (o/'foamRun.log').open('x') as log:
 try:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(o),'-solver','incompressibleFluid'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=2400);rc=r.returncode
 except subprocess.TimeoutExpired:rc='runtime_cap_exceeded'
assert all(sha(s/p)==h for p,h in pins.items());r={'returncode':rc,'elapsed_s':time.monotonic()-start,'source_preserved':True,'end_U_exists':(o/'0.5/U').exists(),'pressure_adopted':False};(o/'native-run-review.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
