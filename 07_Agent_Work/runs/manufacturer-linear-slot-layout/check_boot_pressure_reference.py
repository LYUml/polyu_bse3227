import json,math
from pathlib import Path
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/boot-first-row-four-strip-services';r=json.loads((p/'All Boot Domain Combinations.json').read_text());dims={6:(6.25,5.25),8:(9.375,5.25),10:(12.5,5.25),12:(14.125,7.875)};rows=[]
for label,table in r['tables'].items():
 C,D=[v*.0254 for v in dims[table['inlet_inch']]];area=(C-D)*D+math.pi*D*D/4
 for v in table['rows']:
  q=v['flow_L_s']/1000;delta=v['total_Pa']-v['static_Pa'];vp=.5*1.2*(q/area)**2
  # Explicit display-resolution scenario, not instrument accuracy or manufacturer tolerance.
  vlo=.5*1.2*(max(q-.0005,0)/area)**2;vhi=.5*1.2*((q+.0005)/area)**2
  compatible=not(vhi<delta-.1 or vlo>delta+.1)
  rows.append(dict(catalogue=label,flow_L_s=v['flow_L_s'],stadium_area_m2=area,reported_Pt_minus_Ps_Pa=delta,calculated_velocity_pressure_Pa=vp,display_resolution_intervals_overlap=compatible,residual_Pa=vp-delta))
out=dict(scope='Conditional oval stadium geometry/velocity-pressure reference diagnostic; rho1.2assumed, metricQ+-0.5Ls and eachpressure+-0.05Pa display-resolution scenario only, not source test accuracy or acceptance',rows=rows,compatible_rows=sum(v['display_resolution_intervals_overlap'] for v in rows),row_count=len(rows),accepted=False);(p/'Boot Inlet Pressure Reference Diagnostic.json').write_text(json.dumps(out,indent=2));print(out['compatible_rows'],'of',len(rows),'interval compatible');print('largest',sorted(rows,key=lambda v:abs(v['residual_Pa']),reverse=True)[:3])
