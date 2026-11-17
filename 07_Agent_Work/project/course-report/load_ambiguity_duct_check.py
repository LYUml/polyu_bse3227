from pathlib import Path
import csv,hashlib,json,math
from bsa.duct_equivalent import calculate,select_sizes
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');source=B/'07_Agent_Work/runs/vav-recenter-design-reviewed/delivery/schedule/results.json';raw=source.read_bytes();data=json.loads(raw);R=B/'07_Agent_Work/runs/load-ambiguity-duct-check';R.mkdir(exist_ok=False)
rows=[]
for s in data['sections']:
 i=s['inputs'];q=i['flow_m3_s']/0.9;c=calculate(flow_m3_s=q,width_m=i['width_m'],height_m=i['height_m'],**data['air']);limits=s['limits'];fail=[k for k,v in limits.items() if c[k]>v]
 chosen=dict(width_m=i['width_m'],height_m=i['height_m'],calculation=c)
 if fail:
  candidates=[{k:x[k] for k in ['id','width_m','height_m']} for x in s['selection']['candidates'] if x['width_m']>=i['width_m'] and x['height_m']>=i['height_m']]
  result=select_sizes(candidates=candidates,max_velocity_m_s=limits['actual_velocity_m_s'],max_friction_Pa_m=limits['friction_Pa_m'],max_aspect_ratio=limits['aspect_ratio'],flow_m3_s=q,**data['air']);chosen=result['selected'];assert chosen is not None,s['id']
 assert abs(c['actual_velocity_m_s']-i['flow_m3_s']/(i['width_m']*i['height_m'])/.9)<1e-10
 assert all(chosen['calculation'][k]<=v for k,v in limits.items())
 rows.append({'Section':s['id'],'Sensitivity flow L/s':q*1000,'Current width mm':i['width_m']*1000,'Current height mm':i['height_m']*1000,'Current size sensitivity velocity m/s':c['actual_velocity_m_s'],'Current size sensitivity friction Pa/m':c['friction_Pa_m'],'Failed criteria':';'.join(fail),'Candidate width mm':chosen['width_m']*1000,'Candidate height mm':chosen['height_m']*1000,'Candidate velocity m/s':chosen['calculation']['actual_velocity_m_s'],'Candidate friction Pa/m':chosen['calculation']['friction_Pa_m']})
with (R/'Duct Load Interpretation Sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
review={'scope':'Separate unadopted sizing sensitivity:189 W/m2 interpreted as sensible, existing allocation fractions retained; current coursework unchanged','source_schedule_sha256':hashlib.sha256(raw).hexdigest(),'flow_multiplier':1/.9,'sections':len(rows),'current_sizes_failing':sum(bool(r['Failed criteria']) for r in rows),'velocity_failures':sum('actual_velocity_m_s' in r['Failed criteria'] for r in rows),'friction_failures':sum('friction_Pa_m' in r['Failed criteria'] for r in rows),'all_selected_candidates_pass_declared_section_limits':True,'candidate_basis':'Existing source candidate grid, width and height each >= current size; unchanged selection engine ranks by area/perimeter','engine':'existing bsa.duct_equivalent; fluids1.3.1 MIT Colebrook','geometry_fit_verified':False,'online_ductulator_verified':False,'ADPI_applicability_resolved':False,'design_adopted':False,'design_accepted':False}
assert source.read_bytes()==raw
(R/'review.json').write_text(json.dumps(review,indent=2),encoding='utf-8');print(json.dumps(review,indent=2))
