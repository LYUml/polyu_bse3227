from pathlib import Path
import json,csv
from bsa.manufacturer_adpi import catalogue,screen
from bsa.terminal_performance import calculate
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';d=json.loads((B/'manufacturer-adpi-comparison/comparison.json').read_text());s=d['scenarios'][0]
curves=json.loads((B/'manufacturer-adpi-native-curves/curves.json').read_text());tables=catalogue(Path(d['performance_pdf']))
f=list(Path(d['workflow']).glob('*/allocation.json'));assert len(f)==1
flows={t['id']:t for t in json.loads(f[0].read_text())['terminals']}
vectors={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}
records=[];candidates={}
for t in s['terminals']:
 walls={}
 for name,(dx,dy) in vectors.items():
  x,y=t['center_m'];L=s['diagnostic_lengths_m'][t['id']][name]
  aligned=[((u['center_m'][0]-x)*dx+(u['center_m'][1]-y)*dy)/2 for u in s['terminals'] if u['id']!=t['id'] and abs((u['center_m'][0]-x)*dy-(u['center_m'][1]-y)*dx)<1e-8 and (u['center_m'][0]-x)*dx+(u['center_m'][1]-y)*dy>1e-8]
  if not(aligned and abs(min(aligned)-L)<1e-8):walls[name]=L
 if not walls:continue
 options=[]
 for neck,table in tables.items():
  fails=[];outflow=False
  for cond,loads in [('maximum',(40,60)),('minimum',(20,40))]:
   q=flows[t['id']][cond+'_flow_L_s'];v=calculate(table,q)
   if v['status']!='within_catalogue':
    outflow=True;fails.append(cond+':outside_catalogue');continue
   for direction,L in walls.items():
    for load in loads:
     reading=screen(curves,load,v['T025_m']/L)
     if reading['status']!='paired_curve_threshold_met':fails.append(f'{cond}:{direction}:{load}:{reading["status"]}')
  if not fails:options.append(int(neck))
  records.append({'terminal':t['id'],'neck_inch':int(neck),'wall_directions':';'.join(walls),'maximum_flow_L_s':flows[t['id']]['maximum_flow_L_s'],'minimum_flow_L_s':flows[t['id']]['minimum_flow_L_s'],'wall_only_diagnostic_pass':not fails,'catalogue_flow_exclusion':outflow,'failures':';'.join(fails)})
 candidates[t['id']]=options
out=B/'manufacturer-adpi-wall-neck-diagnosis';out.mkdir(exist_ok=False)
with (out/'wall-neck-cases.csv').open('w',encoding='utf-8',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
r={'scope':'Current80terminal layout wall-limited rays only, all six original Model1400 neck tables; paired manufacturer source diagnostic unchanged. Not whole-room design or physical wall validation.','terminals_with_wall_limited_rays':len(candidates),'neck_terminal_cases':len(records),'terminals_no_neck_can_clear_wall_diagnostic':[k for k,v in candidates.items() if not v],'wall_only_neck_options':candidates,'original8in_wall_passing_terminals':sum(x['wall_only_diagnostic_pass'] for x in records if x['neck_inch']==8),'limitations':['Original ray-boundary proxy retained; actual wall/jet interactions not verified','No heights, criteria, loads or flow changed','Wall-only pass does not clear opposing directions, acoustics, pressure or ADPI','No neck selected or production schedule changed'],'ADPI_verified':False,'design_accepted':False}
(out/'review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r))
