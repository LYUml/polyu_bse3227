"""Bounded static-pressure candidate study using pinned fluids interpolation."""
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from pypdf import PdfReader
from fluids.numerics import interp

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
RUN=ROOT/'07_Agent_Work/runs/vav-manufacturer-capacity'
PDF=RUN/'LMHS_MiniCatalog.pdf'
CAP=RUN/'capacity-screen.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
capacity=json.loads(CAP.read_text())
assert sha(PDF)==capacity['source_sha256']
reader=PdfReader(PDF)
# PDF24/A2-26 visually reviewed. IP columns retained; SI columns independently
# rounded by publisher and must not be combined with exact converted IP flows.
tables={9:[(200,'.005'),(550,'.037'),(900,'.100'),(1160,'.166')],
        10:[(250,'.005'),(700,'.040'),(1100,'.100'),(1450,'.174')],
        12:[(400,'.006'),(1000,'.039'),(1600,'.100'),(2060,'.166')],
        14:[(480,'.005'),(1375,'.043'),(2100,'.100'),(2800,'.178')]}
for page in [23,24]:
    text=reader.pages[page].extract_text()
    for size,values in tables.items():
        block=re.search(r'\n'+str(size)+r'\s*\n(.*?)(?=\n(?:10|12|14|16)\s*\n)',text,re.S).group(1)
        for flow,pressure in values:
            assert re.search(r'\b'+str(flow)+r'\s+\(\d+\)\s+0'+re.escape(pressure)+r'\s',block)
records=[]
factor=Decimal('249.08891') # conventional inch water at 4C, explicit conversion
for row in capacity['rows']:
    for size,values in tables.items():
        option=next(x for x in row['options'] if x['inlet_size']==size)
        for condition,key in [('maximum','maximum_CFM'),('minimum','minimum_CFM')]:
            q=row[key]
            result=dict(id=row['id'],size=size,condition=condition,flow_CFM=q,
                capacity_candidate=option['capacity_candidate'],minimum_static_difference_Pa=None,
                total_pressure_loss_Pa=None)
            if not option['capacity_candidate']:
                result['status']='capacity_rejected'
            elif not values[0][0]<=q<=values[-1][0]:
                result['status']='outside_published_flow_range'
            else:
                pair=next((values[i],values[i+1]) for i in range(len(values)-1)
                          if values[i][0]<=q<=values[i+1][0])
                (x0,y0),(x1,y1)=pair
                expected=Decimal(y0)+(Decimal(str(q))-x0)*(Decimal(y1)-Decimal(y0))/(x1-x0)
                calculated=interp(q,[v[0] for v in values],[float(v[1]) for v in values])
                assert abs(float(expected)-calculated)<1e-12
                result.update(status='conditional_linear_static_estimate',
                    bracket_CFM=[x0,x1],minimum_static_difference_inwg=calculated,
                    minimum_static_difference_Pa=float(expected*factor))
            result['smallest_capacity_candidate']=size==row['smallest_capacity_candidate']
            records.append(result)
smallest=[r for r in records if r['smallest_capacity_candidate']]
assert len(smallest)==40 and all(r['minimum_static_difference_Pa'] is not None for r in smallest)
result=dict(source_sha256=sha(PDF),capacity_sha256=sha(CAP),script_sha256=sha(Path(__file__)),
    source_locator='PDF24/A2-26; duplicate pressure columns checked on PDF25/A2-27',
    source_pressure_page_visually_reviewed=True,independent_Decimal_matches=True,
    interpolation='Piecewise linear explicit design approximation; no extrapolation',
    pressure_type='Minimum inlet-to-discharge static pressure difference, not total-pressure loss',
    inwg_to_Pa=str(factor),records=records,design_accepted=False,full_pressure_verified=False,
    source_conditions='Base standard unit; published sound tables specify 1/2 inch dual-density liner; controls and installation unverified',
    geometry_note='Actual inlet collars are undersized: size9 D=8 7/8in; size10 D=9 7/8in; size12 D=11 7/8in. Casing W/H are not established clear outlet areas; no velocity correction inferred.')
out=RUN/'pressure-screen.json'
assert not out.exists()
out.write_text(json.dumps(result,indent=2))
print(json.dumps({c:[min(r['minimum_static_difference_Pa'] for r in smallest if r['condition']==c),
    max(r['minimum_static_difference_Pa'] for r in smallest if r['condition']==c)]
    for c in ['maximum','minimum']},indent=2))
