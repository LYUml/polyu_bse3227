"""Publish derived candidate calculations, excluding proprietary source PDFs."""
import hashlib
import html
import json
from pathlib import Path
ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
RUN=ROOT/'07_Agent_Work/runs/vav-manufacturer-capacity'
pressure=json.loads((RUN/'pressure-screen.json').read_text())
capacity=json.loads((RUN/'capacity-screen.json').read_text())
assert hashlib.sha256((RUN/'capacity-screen.json').read_bytes()).hexdigest()==pressure['capacity_sha256']
rows=[]
for row in capacity['rows']:
    values=[next(r for r in pressure['records'] if r['id']==row['id'] and r['smallest_capacity_candidate'] and r['condition']==c) for c in ['maximum','minimum']]
    rows.append(dict(id=row['id'],inlet_size_in=row['smallest_capacity_candidate'],
        maximum_flow_L_s=row['maximum_flow_L_s'],minimum_flow_L_s=row['minimum_flow_L_s'],
        maximum_static_estimate_Pa=values[0]['minimum_static_difference_Pa'],
        minimum_static_estimate_Pa=values[1]['minimum_static_difference_Pa'],
        total_pressure_loss_Pa=None,selected_product=None))
body=''.join('<tr>'+''.join('<td>'+html.escape(str(v) if isinstance(v,str) else f'{v:.6f}')+'</td>' for v in [r['id'],r['inlet_size_in'],r['maximum_flow_L_s'],r['minimum_flow_L_s'],r['maximum_static_estimate_Pa'],r['minimum_static_estimate_Pa']])+'</tr>' for r in rows)
report='''<!doctype html><meta charset="utf-8"><title>VAV Manufacturer Candidate Review</title><style>body{font:16px Arial;max-width:1100px;margin:30px auto;line-height:1.5}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #bbb;text-align:right}th{background:#eef}</style><h1>VAV Manufacturer Candidate Review</h1><p>Capacity-compatible LMHS base-unit candidates for the coordinated Connection_Layout. These are unselected equipment candidates. The course design and original sources are preserved.</p><p>Exact source group flows are converted to US CFM using the international foot. Standard capacity and minimum-control ranges are checked on printed A2-4. Minimum static-pressure differences are interpolated within printed A2-26 flow brackets; duplicate pressure columns on A2-27 and independent Decimal arithmetic agree. Linear interpolation is an explicit design approximation, not a native K-Select result.</p><p><strong>Static differences below are not total-pressure losses or fan duty.</strong> Controls, acoustic acceptance, installed clearances, inlet transition, downstream distribution plenum, flexible routes and terminal losses remain unresolved. No candidate is adopted into the IFC. No unknown loss is set to zero.</p><table><tr><th>VAV</th><th>Candidate nominal inlet, in</th><th>Maximum L/s</th><th>Minimum L/s</th><th>Maximum minimum-static estimate, Pa</th><th>Minimum minimum-static estimate, Pa</th></tr>'''+body+'''</table><p>Actual inlet collars are undersized relative to nominal sizes. Casing dimensions are not established clear outlet areas; no static-to-total correction has been inferred. The existing rigid network ends at twenty outlet boundaries, and its incomplete pressure review remains separate.</p><p>Source: <a href="https://www.krueger-hvac.com/file/4034/LMHS_MiniCatalog.pdf">Krueger LMHS MiniCatalog, copyright 2021</a>, printed A2-4, A2-7, A2-26 and A2-27. PDF source SHA256: '''+pressure['source_sha256']+'''</p>'''
out=ROOT/'05_Calculations/Connection_Layout/VAV Manufacturer Candidate Review.html'
assert not out.exists()
out.write_text(report,encoding='utf8')
evidence=dict(groups=20,evaluated_candidate_cases=len(pressure['records']),
    capacity_candidate_counts={str(s):sum(r['inlet_size_in']==s for r in rows) for s in [9,10,12]},
    independent_Decimal_matches=True,source_pages_visually_reviewed=[2,5,24],
    source_sha256=pressure['source_sha256'],source_flow_sha256=capacity['flow_input_sha256'],
    pressure_type=pressure['pressure_type'],interpolation=pressure['interpolation'],rows=rows,
    report_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),full_pressure_verified=False,
    product_selected=False,design_accepted=False)
check=out.with_name('VAV_Manufacturer_Candidate_Check.json')
assert not check.exists()
check.write_text(json.dumps(evidence,indent=2))
agent=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
(agent/'docs/evidence/vav-manufacturer-candidates.json').write_text(json.dumps({k:v for k,v in evidence.items() if k!='rows'},indent=2))
print('Published20 source-flow candidate rows; no total-pressure or equipment acceptance.')
