"""Fresh native guarded source4-6 lookups, composed with the existing ledger."""
import hashlib,json,math
from pathlib import Path
import ifcopenshell
from bsa import duct_fitting_data as fitting
from bsa.duct_fitting_chain import shape_hash
from bsa.rect_round_quantities import calculate
import bsa.rect_round_quantities as reader

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def apply(model,case,result,condition):
    grid_path=BASE/'rect-round-source-study/right-L1-L3.json'
    grid=json.loads(grid_path.read_text())
    proof=json.loads((BASE/'rect-round-source-study/native-queries-units-reviewed.json').read_text())
    assert proof['source_grid_sha256']==sha(grid_path) and proof['native_reader_sha256']==sha(Path(reader.__file__))
    source=BASE.parent/'project/full-network-transition-study/ashrae2021.pdf'
    assert grid['source_sha256']==sha(source)
    table=dict(axes=[dict(quantity=k,values=grid[a]) for k,a in [('Re_divided_by_1e4','Re_axis'),('L_over_D','L_over_D_axis'),('B','B_axis')]],coefficients=grid['coefficients'])
    local=BASE/'rect-round-sourced-design/analytic-inlet-assemblies'
    local_model=ifcopenshell.open(str(local/'VAV Inlet Assemblies.ifc'))
    records=[r for r in proof['records'] if r['stage']=='longer_taper' and r['condition']==condition]
    assert len(records)==20
    for record in records:
        key=tuple(record[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])
        obj=model.by_guid(key[0]);assert record['ifc_sha256']==sha(local/'VAV Inlet Assemblies.ifc')
        assert shape_hash(obj)==shape_hash(local_model.by_guid(key[0]))
        Q=case['port_flows'][key[2]]['flow_m3_s'];geo=calculate(obj,Q,case['air'])
        assert all(geo['source_family_conditions'].values())
        value=fitting.lookup(table,geo['source_quantities']);assert value['coefficient'] is not None
        assert math.isclose(value['coefficient'],float(record['independent_Decimal_coefficient']),rel_tol=1e-12,abs_tol=1e-12)
        value.update(product_guid=key[0],inlet_port_guid=key[1],outlet_port_guid=key[2],
            source_id='ashrae2021-4-6',citation_location='Printed21Fitting4-6,Idelchik1986Diagram5-26;printed22right contraction table,L/D1to3',
            source_document_sha256=grid['source_sha256'],source_grid_sha256=sha(grid_path),
            reference_port_guid=key[2],reference_velocity_m_s=geo['reference_velocity_m_s'],
            reference_velocity_pressure_Pa=geo['reference_velocity_pressure_Pa'],
            signed_tabulated_contribution_Pa=value['coefficient']*geo['reference_velocity_pressure_Pa'],
            native_quantities=geo['source_quantities'],native_geometry=geo,geometry_sha256=shape_hash(obj),
            source_condition_checks=geo['source_family_conditions'],
            independent_Decimal_matches=True,physical_applicability_verified=False,
            pressure_budget_complete=False,design_accepted=False)
        assert not any(tuple(r[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])==key for r in result['table_results'])
        result['table_results'].append(value)
        request=next(r for r in result['data_requests'] if tuple(r[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])==key)
        request.update(recorded_table_result=value,status=fitting.request_status(value),transition_geometry=geo)
    values={tuple(r[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid']):r for r in result['table_results']}
    summaries=[]
    for path in case['boundary_paths']:
        contributions=[];missing=0
        for step in path['steps']:
            if step['kind']!='fitting':continue
            key=tuple(step[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])
            value=values.get(key,{}).get('signed_tabulated_contribution_Pa')
            if value is None:missing+=1
            else:contributions.append(value)
        subtotal=math.fsum(contributions)
        summaries.append(dict(inlet_port_guid=path['inlet_port_guid'],outlet_port_guid=path['outlet_port_guid'],
            known_straight_friction_Pa=path['known_straight_friction_Pa'],supplied_table_contribution_Pa=subtotal,
            unresolved_fitting_path_count=missing,tabulated_plus_separate_straight_Pa=None if missing else path['known_straight_friction_Pa']+subtotal,
            complete_total_pressure_drop_Pa=None))
    result['boundary_paths']=summaries
    result['calculated_table_paths']=sum(r['coefficient'] is not None for r in result['table_results'])
    result['unsupplied_table_paths']=result['unique_fitting_paths']-len(result['table_results'])
    result['sources']['ashrae2021-4-6']=dict(path=str(source),sha256=grid['source_sha256'],locator=grid['locator'])
    assert result['calculated_table_paths']==61
    return result
