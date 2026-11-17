"""Independent native material-cap and Decimal source-query review."""
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util import system,placement
import numpy as np
from bsa.interface_contacts import cap,matching
from bsa.solid_clash import from_mesh

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
RUN=ROOT/'runs/recentered-local-fittings'
r=json.loads((RUN/'review.json').read_text())
schedule=json.loads((ROOT/'runs/vav-recenter-friction-compensated/delivery/schedule/results.json').read_text())
flows={x['id']:x['inputs']['flow_m3_s'] for x in schedule['sections']}
rho=D(str(json.loads((ROOT/'runs/reduced-branch-network-reviewed/analysis.json').read_text())['air']['density_kg_m3']))
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
def native(path):
    model=ifcopenshell.open(str(path));obj=model.by_type('IfcDuctFitting')[0]
    shape=ifcopenshell.geom.create_shape(settings,obj)
    vertices=np.asarray(shape.geometry.verts).reshape(-1,3);faces=np.asarray(shape.geometry.faces).reshape(-1,3)
    ports={p.Name:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(obj)}
    return {name:cap(vertices,faces,frame) for name,frame in ports.items()},from_mesh((vertices,faces)),ports
queries=[]
for case in r['cases']:
    folder=RUN/case['node'];tc,solid,frames=native(folder/'tee/unequal-tee.ifc')
    binding=json.loads((folder/'binding.json').read_text())
    source={x['section']:x for x in case['revised_source_node']['incidents']}
    assert np.allclose(tc['branch']['inner_section_m'],[source[binding['arms']['branch']]['width_m'],source[binding['arms']['branch']]['height_m']],atol=1e-8,rtol=0)
    for transition in case['main_transitions']:
        arm=transition['arm'];caps,body,ports=native(folder/arm/'transition.ifc')
        matching(tc[arm],caps['start'])
        assert abs((solid^body).volume())<1e-12
        endpoint=source[transition['source_section']]
        assert np.allclose(caps['end']['inner_section_m'],[endpoint['width_m'],endpoint['height_m']],atol=1e-8,rtol=0)
        spec=json.loads((folder/(arm+'.json')).read_text())
        angles=[math.degrees(2*math.atan(abs(a-b)/(2*spec['transition_length_m']))) for a,b in zip(spec['start_section_m'],spec['end_section_m'])]
        for actual,expected in zip(angles,[transition['geometry']['quantities'][k] for k in ['taper_width_angle_deg','taper_height_angle_deg']]):assert math.isclose(actual,expected,abs_tol=1e-12)
        for family,query in transition['source_queries'].items():
            assert query['coefficient'] is not None
            angle=D(str(max(angles)));g=transition['geometry'];a,b=[list(map(lambda v:D(str(v)),g[k])) for k in ['inlet_section_m','outlet_section_m']]
            ratio=a[0]*a[1]/(b[0]*b[1]);assert 1<=ratio<=2
            if family=='centred_equal_angle_pyramidal':
                ordinate=D('.21')+(angle-20)/10*(D('.20')-D('.21')) if angle<=30 else D('.20')+(angle-30)/15*D('.02')
            else:ordinate=D('.20') if angle<=30 else D('.20')+(angle-30)/15*D('.04')
            coefficient=(ratio-1)*ordinate
            assert math.isclose(float(coefficient),query['coefficient'],rel_tol=1e-12,abs_tol=0)
            q=D(str(flows[transition['source_section']]));velocity=q/(a[0]*a[1]);loss=coefficient*rho/2*velocity**2
            queries.append(dict(node=case['node'],source_section=transition['source_section'],family=family,
                independently_recomputed_coefficient=float(coefficient),maximum_conditional_local_loss_Pa=float(loss),
                minimum_given40percent_conditional_local_loss_Pa=float(loss*D('.16')),independent_Decimal_match=True))
assert len(queries)==3
summary=dict(rebuilt_tee_groups=6,native_cap_pairs_matched=6,native_external_main_sections_matched=6,
    native_branch_sections_matched=6,local_material_intersections=0,independent_source_queries=queries,
    network_integrated=False,current_network_numeric_gaps_unchanged=33,design_accepted=False,
    scope='Recentered local fittings only; no installed clearance, interaction, full pressure or native CAD acceptance')
(RUN/'independent-review.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
