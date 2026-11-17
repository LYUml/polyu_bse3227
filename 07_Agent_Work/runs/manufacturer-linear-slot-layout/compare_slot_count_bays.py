from pathlib import Path
import subprocess,sys,json
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');src=(base/'select_slot_count.py').read_text()
for name in ['bay-two-by-six','bay-2-by-4','bay-2-by-5','bay-3-by-4']:
 s=src.replace('manufacturer-linear-slot-layout/boundary-corrected',f'manufacturer-linear-slot-layout/{name}');p=base/name/'select_slot_count.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True,capture_output=True);r=json.loads((p.parent/'slot-count-selection.json').read_text());print(name,r['terminals_passing'],r['terminals_with_flow_domain_gap'], 'bay pass',sum(v['id'].startswith('bay-') and v['best']['all_checks_pass'] for v in r['results']))
