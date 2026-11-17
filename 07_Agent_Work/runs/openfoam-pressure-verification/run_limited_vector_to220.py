from pathlib import Path
import json,os,subprocess
b=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=b/'actual-family-1-resolution-limited-vector'
(c/'system/controlDict').write_text('FoamFile {format ascii;class dictionary;object controlDict;}\napplication foamRun;solver incompressibleFluid;startFrom startTime;startTime 20;stopAt endTime;endTime 220;deltaT 1;writeControl timeStep;writeInterval 110;writeFormat ascii;writePrecision 17;runTimeModifiable false;\n')
s=(b/'actual-family-1-resolution-mixed-order/native-history-to420.json').read_text().replace('actual-family-1-resolution-mixed-order',c.name).replace('mixed-startup-review.json','limited-vector-inputs.json');m=json.loads(s);m['expected_window']=[21,220];(c/'native-history-to220.json').write_text(json.dumps(m,indent=2)+'\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (c/'foamRun-to220.log').open('x') as log:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(c)],env=e,stdout=log,stderr=subprocess.STDOUT)
print('native_returncode',r.returncode)
