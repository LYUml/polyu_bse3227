from pathlib import Path
import sys,os,subprocess,json,argparse
from bsa import drawing_layout
p=argparse.ArgumentParser();p.add_argument('--autocad',required=True);a=p.parse_args()
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';R=P/'07_Agent_Work/project/general-drawing'
assert os.environ.get('BSA_PROJECT_ROOT') and Path(os.environ['BSA_PROJECT_ROOT']).resolve()==P.resolve()
for tag in ['01-10','11-20']:
 recipe=R/f'current-terminal-systems-{tag}.json';out=B/f'current-source-terminal-systems-{tag}-native'
 with (B/'current-source-system-diagrams'/f'native-{tag}-execution.log').open('x',encoding='utf-8') as log:
  r=subprocess.run([sys.executable,'-m','bsa.drawing_access','run',str(recipe),'--out',str(out),'--autocad',a.autocad],stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0,tag
 result=drawing_layout.verify(recipe,out);assert result['integrity_pass'] and result['native_reopen_pass']
 (out/'independent-native-inspect.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'sheet':tag,'native_reopen_pass':True,'entities':result['editable_entities'],'artifacts':result['artifacts']}),flush=True)
