"""Source-native capacity screening; never substitutes a static rating for loss."""
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from pypdf import PdfReader

ROOT = Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
RUN = ROOT/'07_Agent_Work/runs/vav-manufacturer-capacity'
PDF = RUN/'LMHS_MiniCatalog.pdf'
SOURCE = ROOT/'07_Agent_Work/runs/recentered-vav-connection-schedule/review.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# Visually checked PDF page2, printed A2-4; base standard units, not heat.
capacity = [(4,230,40),(5,360,62),(6,515,89),(7,700,121),
            (8,920,159),(9,1160,201),(10,1430,248),(12,2060,357),
            (14,2800,486),(16,3660,634),(22,7000,1212)]
text = PdfReader(PDF).pages[1].extract_text()
for size,maximum,minimum in capacity:
    assert f'{size} {maximum} {minimum} ' in text
source = json.loads(SOURCE.read_text())
# Exact international foot, US CFM. Use original precise flows, never CSV display.
litres_per_cfm = Decimal('0.3048')**3*Decimal(1000)/Decimal(60)
rows=[]
for row in source['rows']:
    maximum = Decimal(str(row['maximum_flow_L_s']))/litres_per_cfm
    minimum = Decimal(str(row['minimum_flow_L_s']))/litres_per_cfm
    options=[]
    for size,cap,low in capacity:
        options.append(dict(inlet_size=size,capacity_CFM=cap,standard_minimum_CFM=low,
            maximum_capacity_pass=maximum<=cap,standard_minimum_pass=minimum>=low,
            capacity_candidate=maximum<=cap and minimum>=low))
    feasible=[o for o in options if o['capacity_candidate']]
    assert feasible
    rows.append(dict(id=row['id'],maximum_flow_L_s=row['maximum_flow_L_s'],
        minimum_flow_L_s=row['minimum_flow_L_s'],maximum_CFM=float(maximum),
        minimum_CFM=float(minimum),options=options,
        smallest_capacity_candidate=feasible[0]['inlet_size'],
        selected_product=None,actual_pressure_loss_Pa=None))
assert len(rows)==20 and len({r['id'] for r in rows})==20
result=dict(source_url='https://www.krueger-hvac.com/file/4034/LMHS_MiniCatalog.pdf',
    source_sha256=sha(PDF),locator='PDF page2, printed A2-4, standard unit capacities',
    source_page_visually_reviewed=True,flow_input_sha256=sha(SOURCE),
    script_sha256=sha(Path(__file__)),CFM_to_L_s=str(litres_per_cfm),
    configuration='Base standard no-reheat candidate only; not installed selection',
    rows=rows,capacity_screen_pass=True,full_pressure_verified=False,
    pressure_basis='Catalogue AHRI minimum delta Ps is inlet-to-discharge static difference at rated test flow; not a constant total-pressure loss at project flow',
    unresolved=['Actual unit pressure at both project flows','Control and acoustic selection',
        'Round inlet to existing rectangular network transition and loss',
        'Rectangular discharge to four flexible outlets, geometry and losses',
        'Installed enclosure, service access and elevation','Final equipment selection'],
    design_accepted=False)
output=RUN/'capacity-screen.json'
assert not output.exists(), 'Preserve prior evidence'
output.write_text(json.dumps(result,indent=2))
counts={size:sum(r['smallest_capacity_candidate']==size for r in rows) for size,_,_ in capacity}
print(json.dumps(dict(groups=len(rows),candidate_counts=counts,
    max_CFM_range=[min(r['maximum_CFM'] for r in rows),max(r['maximum_CFM'] for r in rows)],
    min_CFM_range=[min(r['minimum_CFM'] for r in rows),max(r['minimum_CFM'] for r in rows)],
    actual_pressure_loss='unknown',design_accepted=False),indent=2))
