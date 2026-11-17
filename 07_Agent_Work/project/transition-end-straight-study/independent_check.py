import json, math, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];file=root/'runs/transition-end-straight-study/fitting-data.json';d=json.loads(file.read_text());air=json.loads((Path(d['source_analysis'])/'analysis.json').read_text())['air'];previous=json.loads((root/'runs/full-network-transition-fitting-data/fitting-data.json').read_text())
assert d['table_results']==previous['table_results'] and d['boundary_paths']==previous['boundary_paths']
residuals=[];n=0
for fitting in d['transition_end_straight_study']:
 assert not fitting['added_to_pressure_paths'] and not fitting['physical_applicability_verified']
 for row in fitting['ends']:
  w,h,q,length=[row[k] for k in ('width_m','height_m','flow_m3_s','length_m')];c=row['calculation'];de=1.30*(w*h)**.625/(w+h)**.25;velocity=4*q/(math.pi*de**2);re=air['density_kg_m3']*velocity*de/air['viscosity_Pa_s'];f=c['darcy_factor'];residual=1/math.sqrt(f)+2*math.log10(air['roughness_m']/de/3.7+2.51/(re*math.sqrt(f)));residuals.append(abs(residual))
  expected=f*air['density_kg_m3']*velocity**2*length/(2*de)
  assert math.isclose(expected,row['developed_flow_study_friction_Pa'],abs_tol=1e-12,rel_tol=1e-12)
  assert math.isclose(re,c['reynolds'],abs_tol=1e-9,rel_tol=1e-12)
  n+=1
assert n==62 and max(residuals)<1e-10 and not d['pressure_budget_complete'] and d['critical_path'] is None
out=dict(transitions=len(d['transition_end_straight_study']),ends=n,max_colebrook_residual=max(residuals),all_darcy_arithmetic_agree=True,table_results_and_pressure_paths_unchanged=True,pressure_budget_complete=False,design_accepted=False,source_record_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
Path(__file__).with_name('independent-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
