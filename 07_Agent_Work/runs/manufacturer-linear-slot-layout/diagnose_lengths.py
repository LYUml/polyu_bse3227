import json
from pathlib import Path
from fluids.numerics import interp
p=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout/uniform-main-15-rows');a=json.loads((p/'allocation.json').read_text());r=json.loads((p/'slot-count-selection-33-samples.json').read_text());result=[]
for t,v in zip(a['terminals'],r['results']):
 if v['best']['all_checks_pass']:continue
 options=[]
 for label,table in r['tables'].items():
  rows=table['rows'];qm=t['maximum_flow_L_s']/1.2192;qn=t['minimum_flow_L_s']/1.2192
  if not rows[0]['flow_L_s_m']<=qn<=qm<=rows[-1]['flow_L_s_m']:continue
  throws=[interp(q,[s['flow_L_s_m'] for s in rows],[s['T050_m'] for s in rows]) for q in [qm,qn]]
  lo=max(throws[0]/1.444,throws[1]/1.757);hi=min(throws)/.506
  if lo<=hi:options.append(dict(product=label,L_low_m=lo,L_high_m=hi))
 result.append(dict(id=t['id'],options=options));print(t['id'],[(x['product'],round(x['L_low_m'],2),round(x['L_high_m'],2)) for x in options])
(p/'necessary-L-intervals.json').write_text(json.dumps(dict(scope='Conservative 0.001-grid paired-curve ratio bounds, necessary common scalar L only, not physical layout or acceptance',results=result),indent=2))
