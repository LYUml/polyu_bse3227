from pathlib import Path
import subprocess,sys
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');src=(base/'change_bay.py').read_text()
for nx,ny in [(2,4),(2,5),(3,4)]:
 name=f'bay-{nx}-by-{ny}';s=src.replace('(2,6)',f'({nx},{ny})').replace('bay-two-by-six',name);p=base/f'change_{name}.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True,capture_output=True)
 for script in ['check_finite_slots.py','select_width.py']:subprocess.run([sys.executable,str(base/name/script)],check=True,capture_output=True)
 import json
 r=json.loads((base/name/'width-selection.json').read_text());a=json.loads((base/name/'allocation.json').read_text());print(name,'total',len(a['terminals']),'pass',r['terminals_passing'],'flow_gap_terminals',r['terminals_with_flow_domain_gap'])
