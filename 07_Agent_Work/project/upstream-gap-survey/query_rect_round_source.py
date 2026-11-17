"""Bounded source queries on actual old/new native geometry, with Decimal replay."""
import hashlib,itertools,json,math
from decimal import Decimal
from pathlib import Path
import ifcopenshell
from bsa.rect_round_quantities import calculate
from bsa.duct_fitting_data import lookup
import bsa.rect_round_quantities as reader

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
OUT=BASE/'rect-round-source-study';source=json.loads((OUT/'right-L1-L3.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
table=dict(axes=[dict(quantity=k,values=source[a]) for k,a in [('Re_divided_by_1e4','Re_axis'),('L_over_D','L_over_D_axis'),('B','B_axis')]],coefficients=source['coefficients'])
def independent(quantities):
    dimensions=[]
    for axis in table['axes']:
        x=Decimal(str(quantities[axis['quantity']]));values=list(map(lambda v:Decimal(str(v)),axis['values']))
        assert values[0]<=x<=values[-1]
        i=next(i for i in range(len(values)-1) if values[i]<=x<=values[i+1])
        weight=(x-values[i])/(values[i+1]-values[i]);dimensions.append((i,weight))
    result=Decimal(0)
    for bits in itertools.product([0,1],repeat=3):
        coefficient=table['coefficients'];weight=Decimal(1)
        for (i,w),bit in zip(dimensions,bits):coefficient=coefficient[i+bit];weight*=w if bit else 1-w
        result+=Decimal(str(coefficient))*weight
    return result
records=[]
for stage,directory in [('original','rect-round-cadquery'),('longer_taper','rect-round-sourced-design')]:
    path=BASE/directory/'analytic-inlet-assemblies/VAV Inlet Assemblies.ifc'
    model=ifcopenshell.open(str(path));cases=json.loads((path.parent/'author-review.json').read_text())['cases']
    for condition in ['maximum','minimum']:
        flow=json.loads((BASE/'inlet-integrated-network/pressure'/condition/'analysis.json').read_text())
        for row in cases:
            obj=model.by_guid(row['guid']);Q=flow['port_flows'][row['ports']['circle']['guid']]['flow_m3_s']
            geo=calculate(obj,Q,flow['air']);assert all(geo['source_family_conditions'].values())
            result=lookup(table,geo['source_quantities'])
            record=dict(stage=stage,condition=condition,id=row['id'],product_guid=obj.GlobalId,
                inlet_port_guid=row['ports']['rectangle']['guid'],outlet_port_guid=row['ports']['circle']['guid'],
                geometry=geo,lookup=result,ifc_sha256=sha(path),physical_applicability_verified=False)
            if stage=='original':assert result['coefficient'] is None
            else:
                assert result['coefficient'] is not None
                check=independent(geo['source_quantities'])
                assert math.isclose(float(check),result['coefficient'],rel_tol=1e-12,abs_tol=1e-12)
                record.update(independent_Decimal_coefficient=str(check),
                    signed_tabulated_contribution_Pa=result['coefficient']*geo['reference_velocity_pressure_Pa'])
            records.append(record)
assert len(records)==80
report=dict(source_document_sha256=source['source_sha256'],source_grid_sha256=sha(OUT/'right-L1-L3.json'),
    source_locator=source['locator'],native_reader_sha256=sha(Path(reader.__file__)),
    source_condition='Contraction Ao<A1 and H<D; centred ruled slot-to-round interpretation; no extrapolation',
    native_old_queries_rejected=40,native_new_queries_supported=40,independent_Decimal_matches=True,
    reference='Circular outlet Ao/Vo, not rectangular inlet velocity',records=records,
    network_pressure_adopted=False,full_pressure_verified=False,design_accepted=False)
target=OUT/'native-queries-units-reviewed.json';assert not target.exists();target.write_text(json.dumps(report,indent=2))
new=[r for r in records if r['stage']=='longer_taper']
print(json.dumps(dict(original_rejected=40,new_supported=40,independent_Decimal_matches=True,
    coefficient_range=[min(r['lookup']['coefficient'] for r in new),max(r['lookup']['coefficient'] for r in new)],
    maximum_flow_contribution_Pa=[min(r['signed_tabulated_contribution_Pa'] for r in new if r['condition']=='maximum'),max(r['signed_tabulated_contribution_Pa'] for r in new if r['condition']=='maximum')])))
