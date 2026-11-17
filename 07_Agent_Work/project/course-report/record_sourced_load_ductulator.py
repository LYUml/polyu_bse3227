"""Record observed browser UI outputs; independently bind every query to source."""
from pathlib import Path
import json,csv,math
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=B/'07_Agent_Work/runs/course-sourced-load-candidate'
d=json.loads((R/'schedule-corridor/results.json').read_text());queries={}
for r in d['sections']:
    i=r['inputs'];key=(i['flow_m3_s']*1000,i['width_m']*1000,i['height_m']*1000,r['limits']['actual_velocity_m_s'],r['limits']['friction_Pa_m']);queries.setdefault(key,[]).append(r['id'])
velocity=[9.9,10,6.6,6.3,5,7.1,5.7,4.9,9.6,7.3,6.2,5.5,7.3,6.1,5.3,8.4,6.9,6.1,5.2,6.9,5.7,4.9,6.4,5.6,5.3,5.3,5.4,5.4,5.5,5.2,4.9,5,5.1,5.3,5.3,5.7]
friction=[.859,.962,1.011,1.136,1.012,1.198,.880,.973,1.057,1.191,1.050,1.143,1.191,.997,1.109,1.164,1.105,1.082,1.094,1.105,.886,.970,1.058,1.154,1.124,1.129,1.137,1.144,1.143,1.006,.926,1.026,1.032,1.133,1.126,1.200]
assert len(queries)==len(velocity)==len(friction)==36
observed={}
for (query,ids),v,f in zip(queries.items(),velocity,friction):
    q,w,h,vcap,fcap=query;assert v==float(format(q/1000/(w*h/1e6),'.1f'));assert f+.0005<fcap
    for ident in ids:observed[ident]=(query,v,f)
assert len(observed)==47;rows=[]
for section in d['sections']:
    name=section['id'];(q,w,h,vcap,fcap),v,f=observed[name];calc=section['calculation'];assert calc['actual_velocity_m_s']<=vcap+1e-12
    rows.append(dict(zip(['Section','Flow L/s','Width mm','Height mm','Exact geometric velocity m/s','Online velocity display m/s','Online friction display Pa/m','Formula friction Pa/m','Relative online minus formula','Velocity limit m/s','Friction cap Pa/m'],[name,q,w,h,calc['actual_velocity_m_s'],format(v,'.1f'),format(f,'.3f'),calc['friction_Pa_m'],f/calc['friction_Pa_m']-1,vcap,fcap])))
with (R/'Online Ductulator Check.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
summary=dict(scope='Actual browser fixed-section OnlineDuctulator check for unadopted150W/m2 candidate; not full pressure or statutory conformity',url='https://ductulator.com/metric/',version='V1.0.8',sections=47,unique_input_queries=36,all_input_dimensions_and_units_observed=True,all47_displayed_velocities_match_exact_geometry_rounding=True,all47_displayed_friction_below_source_caps_including_half_last_digit=True,maximum_online_friction_Pa_m=max(friction),relative_friction_difference_range=[min(r['Relative online minus formula'] for r in rows),max(r['Relative online minus formula'] for r in rows)],formula_and_website_not_assumed_equal=True,website_air_properties_not_independently_verified=True,engine_code_copied=False,design_accepted=False)
(R/'Online Ductulator Check.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
