from pathlib import Path
import json,hashlib
from bsa.manufacturer_adpi import catalogue,screen
from bsa.terminal_performance import calculate
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs'
d=json.loads((B/'manufacturer-adpi-comparison/comparison.json').read_text());s=d['scenarios'][0]
curves=json.loads((B/'manufacturer-adpi-native-curves/curves.json').read_text());rows=catalogue(Path(d['performance_pdf']))['8']
alloc=json.loads((Path(d['workflow'])/'air-allocation/allocation.json').read_text()) if (Path(d['workflow'])/'air-allocation/allocation.json').exists() else None
if alloc is None:
 candidates=list(Path(d['workflow']).glob('*/allocation.json'));assert len(candidates)==1
 alloc=json.loads(candidates[0].read_text())
flows={t['id']:t for t in alloc['terminals']}
directions={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}
prepared=[];opp=0;wall=0
for t in s['terminals']:
 for condition,loads in [('maximum',(40,60)),('minimum',(20,40))]:
  q=flows[t['id']][condition+'_flow_L_s'];v=calculate(rows,q)
  assert v['status']=='within_catalogue'
  for name,(dx,dy) in directions.items():
   x,y=t['center_m'];L=s['diagnostic_lengths_m'][t['id']][name]
   aligned=[((u['center_m'][0]-x)*dx+(u['center_m'][1]-y)*dy)/2 for u in s['terminals'] if u['id']!=t['id'] and abs((u['center_m'][0]-x)*dy-(u['center_m'][1]-y)*dx)<1e-8 and (u['center_m'][0]-x)*dx+(u['center_m'][1]-y)*dy>1e-8]
   opposing=bool(aligned and abs(min(aligned)-L)<1e-8)
   opp+=opposing;wall+=not opposing
   prepared.append((t['id'],condition,name,L,v['T025_m'],loads,opposing))
results=[]
for n in range(301):
 drop=n/100;fails=0;wallfails=0;ids=set()
 for tid,cond,name,L,throw,loads,opposing in prepared:
  effective=L+(drop if opposing else 0)
  if any(screen(curves,load,throw/effective)['status']!='paired_curve_threshold_met' for load in loads):
   fails+=1;wallfails+=not opposing;ids.add(tid)
 results.append({'hypothetical_downward_distance_m':drop,'failed_directional_operating_cases':fails,'failed_wall_limited_cases':wallfails,'terminals_with_any_failure':len(ids)})
best=min(results,key=lambda r:r['failed_directional_operating_cases'])
out=B/'manufacturer-adpi-length-sensitivity';out.mkdir(exist_ok=False)
receipt={'source_guide_sha256':hashlib.sha256((P/'07_Agent_Work/project/adpi-manufacturer-study/GRD_Engineering.pdf').read_bytes()).hexdigest(),'source_pages_actually_rendered_and_viewed':[10,13],'scope':'Existing 80-terminal nominal8in scenario only; diagnostic ambiguity study, not adopted length rule or actual height','source_issue':'Guide prose includes downward mixed-jet travel to occupied zone; adjacent table is abbreviated. Existing length proxy was planar. Installation and definition applicability unresolved.','case_count':640,'opposing_midplane_cases':opp,'wall_limited_cases':wall,'sweep':'0 to 3m inclusive in0.01m increments; hypothetical parameter only, not building dimensions','unchanged':['thermal load','airflow','terminal positions','catalogue','paired source curves','stroke margins','wall-limited lengths'],'baseline':results[0],'best_sample':best,'any_whole_scenario_pass':any(r['failed_directional_operating_cases']==0 for r in results),'sampled_results':results,'ADPI_verified':False,'design_accepted':False}
(out/'review.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='sampled_results'}))
