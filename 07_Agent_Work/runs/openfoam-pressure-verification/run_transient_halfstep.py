from pathlib import Path
import json,shutil,hashlib,os,subprocess,time
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');assert Path(os.environ['BSA_PROJECT_ROOT']).resolve()==P.resolve()
B=P/'07_Agent_Work/runs/openfoam-pressure-verification';source=B/'plenum-family-1-transient-kepsilon-pilot';out=B/'plenum-family-1-transient-kepsilon-halfstep'
prepared=out.exists()
if prepared:assert not (out/"foamRun.log").exists()
else:out.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(source)):sha(p) for folder in ['0','constant','system'] for p in (source/folder).rglob('*') if p.is_file()}
if not prepared:
 for folder in ['0','constant','system']:shutil.copytree(source/folder,out/folder)
control=out/'system/controlDict';text=control.read_text();assert ('deltaT 0.00025;' in text or 'deltaT 0.000125;' in text)
control.write_text(text.replace('deltaT 0.00025;','deltaT 0.000125;').replace('writeInterval 20;','writeInterval 40;'),encoding='ascii')
changed=[p for p,h in pins.items() if sha(out/p)!=h];assert [Path(x).as_posix() for x in changed]==['system/controlDict'],changed
policy={'scope':'Same physical end time0.005s, same source mesh/initial fields/model/schemes/BCs and observers; half deltaT only','source_case':'plenum-family-1-transient-kepsilon-pilot','source_input_sha256':pins,'changed_inputs':changed,'deltaT_s':.000125,'physical_end_time_s':.005,'steps':40,'runtime_budget_s':180,'full_temporal_independence_claimed':False,'pressure_adopted':False,'design_accepted':False}
(out/'comparison-inputs.json').write_text(json.dumps(policy,indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
start=time.monotonic()
with (out/'foamRun.log').open('x',encoding='utf-8') as log:
 r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(out),'-solver','incompressibleFluid'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert all(sha(source/p)==h for p,h in pins.items())
review={'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start,'source_inputs_preserved':True,'saved_final_time_exists':(out/'0.005/U').exists(),'pressure_adopted':False,'design_accepted':False}
(out/'native-run-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review),flush=True)
