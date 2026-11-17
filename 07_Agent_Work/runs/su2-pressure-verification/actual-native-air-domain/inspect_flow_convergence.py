"""Inspect actual saved CFD history; never grant engineering acceptance."""
import csv,json,math,hashlib
from pathlib import Path
p=Path(__file__).parent
history=p/'wall-only-solve/wall-only-history.csv'
basis=json.loads((p/'flow-boundary-review.json').read_text())
with history.open() as f:
 reader=csv.DictReader(f,skipinitialspace=True);rows=[]
 for raw in reader:
  try:row={k.strip().strip('"'):float(v) for k,v in raw.items()}
  except (ValueError,TypeError,AttributeError):continue
  if all(math.isfinite(v) for v in row.values()):rows.append(row)
last=rows[-1];boundaries=[]
for b in basis['boundaries']:
 name=b['marker'];signed=last['Avg_Massflow('+name+')'];target=b['mass_flow_kg_s']*(1 if b['direction']=='SINK' else -1)
 boundaries.append({'marker':name,'target_signed_mass_flow_kg_s':target,'actual_signed_mass_flow_kg_s':signed,'relative_target_error':abs(signed-target)/abs(target)})
inlet=next(x for x in boundaries if x['marker']=='inlet');balance=abs(sum(x['actual_signed_mass_flow_kg_s'] for x in boundaries))/abs(inlet['actual_signed_mass_flow_kg_s']);window=rows[-100:];pressures={}
for b in boundaries:
 name=b['marker'];key='Avg_TotalPress('+name+')';v=[row[key] for row in window];pressures[name]={'last_Pa':v[-1],'window_range_Pa':max(v)-min(v)}
r={'iteration':int(last['Inner_Iter']),'basis_analysis_sha256':basis['analysis_sha256'],'boundaries':boundaries,'relative_global_mass_imbalance':balance,'last_100_iteration_total_pressure_variation':pressures,'numerical_target_assumptions':{'relative_flow_error':.001,'relative_mass_imbalance':.001,'scope':'proposed numerical convergence targets, not statutory or manufacturer limits'},'flow_target_met':all(x['relative_target_error']<=.001 for x in boundaries),'global_mass_target_met':balance<=.001,'pressure_accepted':False,'engineering_accepted':False}
(p/'wall-only-solve/flow-convergence-review.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
