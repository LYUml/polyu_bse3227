"""Revise candidate inlet ducts using existing course velocity and native capacity."""
import hashlib
import json
import math
from pathlib import Path
from decimal import Decimal

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
RUN=ROOT/'07_Agent_Work/runs/vav-manufacturer-capacity'
CAP=RUN/'capacity-screen.json'
PRS=RUN/'pressure-screen.json'
BASIS=ROOT/'05_Calculations/data/course_workshop_basis.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
capacity=json.loads(CAP.read_text()); pressure=json.loads(PRS.read_text())
limit=json.loads(BASIS.read_text())['low_pressure_office_supply_velocity_max_ms']['branch']
assert limit==8
rows=[]
for row in capacity['rows']:
    options=[]
    for option in row['options']:
        size=option['inlet_size']
        if size>16:continue # size22 is rectangular, not a circular candidate
        diameter=size*.0254
        velocity=row['maximum_flow_L_s']/1000/(math.pi*diameter**2/4)
        # Independent Decimal area arithmetic; no rounding before selection.
        ref=Decimal(str(row['maximum_flow_L_s']))/1000/(Decimal(str(math.pi))*(Decimal(size)*Decimal('.0254'))**2/4)
        assert abs(float(ref)-velocity)<1e-12
        options.append(dict(size_in=size,nominal_duct_diameter_m=diameter,
            maximum_duct_velocity_m_s=velocity,capacity_pass=option['capacity_candidate'],
            velocity_pass=velocity<=limit,combined_pass=option['capacity_candidate'] and velocity<=limit))
    feasible=[o for o in options if o['combined_pass']]
    assert feasible
    chosen=feasible[0]
    size=chosen['size_in']
    assert size in [12,14]
    # Actual nominal-to-collar differences and casing sizes from viewed A2-7.
    collar=(size-.125)*.0254
    values=[next(v for v in pressure['records'] if v['id']==row['id'] and v['size']==size and v['condition']==c) for c in ['maximum','minimum']]
    assert all(v['status']=='conditional_linear_static_estimate' for v in values)
    rows.append(dict(id=row['id'],capacity_only_size_in=row['smallest_capacity_candidate'],
        revised_candidate_size_in=size,maximum_flow_L_s=row['maximum_flow_L_s'],
        minimum_flow_L_s=row['minimum_flow_L_s'],options=options,
        maximum_duct_velocity_m_s=chosen['maximum_duct_velocity_m_s'],
        actual_collar_diameter_m=collar,
        maximum_collar_velocity_m_s=row['maximum_flow_L_s']/1000/(math.pi*collar**2/4),
        recommended_upstream_straight_m=3*chosen['nominal_duct_diameter_m'],
        recommended_control_access_m=.4572,
        casing_length_m=15.5*.0254,casing_width_m=(16 if size==12 else 20)*.0254,
        casing_height_m=(15 if size==12 else 17.5)*.0254,
        maximum_minimum_static_estimate_Pa=values[0]['minimum_static_difference_Pa'],
        minimum_minimum_static_estimate_Pa=values[1]['minimum_static_difference_Pa'],
        installed_geometry_verified=False,total_pressure_loss_Pa=None))
result=dict(source_capacity_sha256=sha(CAP),source_pressure_sha256=sha(PRS),
    course_basis_sha256=sha(BASIS),catalogue_sha256=sha(RUN/'LMHS_MiniCatalog.pdf'),
    installation_manual_sha256=sha(RUN/'SDIOM.pdf'),script_sha256=sha(Path(__file__)),
    policy='Apply existing course branch-duct8m/s to proposed nominal circular inlet duct; not a claimed manufacturer internal collar limit. Smallest combined capacity/control/duct-velocity candidate.',
    installation_source='SDIOM PDF6 Step2A:3D straight recommended; PDF3 ServiceAccess:18in control clearance recommended. Local-code applicability and installed clearance unverified.',
    source_dimension_locator='LMHS MiniCatalog PDF5 printed A2-7; casing only, excludes unverified controls, connection and access envelopes',
    rows=rows,full_pressure_verified=False,product_selected=False,design_accepted=False)
out=RUN/'inlet-revision.json'; assert not out.exists()
out.write_text(json.dumps(result,indent=2))
print(json.dumps(dict(groups=len(rows),counts={s:sum(r['revised_candidate_size_in']==s for r in rows) for s in [12,14]},
    duct_velocity_range=[min(r['maximum_duct_velocity_m_s'] for r in rows),max(r['maximum_duct_velocity_m_s'] for r in rows)],
    collar_over8=[r['id'] for r in rows if r['maximum_collar_velocity_m_s']>8],
    installed_geometry_verified=False),indent=2))
