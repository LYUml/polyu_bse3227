"""Actual-endpoint two-family transition candidate using existing native author."""
import hashlib
import json
import math
from pathlib import Path
import uuid
import numpy as np
import ifcopenshell
from ifcopenshell.util import placement,system,element
from bsa import rectangular_transition as author
from bsa.duct_transition_quantities import calculate,family_check
from bsa.duct_fitting_data import lookup

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
OUT=ROOT/'runs/staged-transition-candidate-reviewed'
OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=RUN/'Supply Network.ifc';before=sha(source)
model=ifcopenshell.open(str(source));guid='0rXojppeTH0BTVX2pgkVrd'
obj=model.by_guid(guid)
geo=calculate(obj,'start','end');assert geo['flow_change']=='contraction'
start=np.array(geo['inlet_section_m']);end=np.array(geo['outlet_section_m'])
delta=start-end;assert np.all(delta>0) and delta[0]>delta[1]
mid=start-min(delta)
q=geo['quantities'];taper=q['taper_length_m'];split=min(delta)/max(delta)
assert 0<split<1
base=placement.get_local_placement(obj.ObjectPlacement)
offset=element.get_psets(obj)['BSA_DesignInputs']['SectionOffset_m']
straight=(q['inlet_straight_length_m']+q['outlet_straight_length_m'])/4
assert straight>author.EXTENSION_M
lengths=[taper*split,taper*(1-split)]
families=['centred_equal_angle_pyramidal','centred_one_plane']
positions=[base.copy(),base.copy()]
positions[1][:3,3]+=base[:3,2]*(lengths[0]+2*straight)
basis=json.loads((RUN/'one-plane-source-extension-reviewed/basis.json').read_text())
tables=[next(t for t in basis['tables'] if t.get('transition_family')==f) for f in families]
# Printed19 reviewed contraction rows also supply the unambiguous15-degree
# column. Keep the actual slightly-below30 native angle, with no snapping.
tables[1]['axes'][1]['values']=[15.,30.,45.]
tables[1]['coefficients']=[[0.,0.,0.],[.20,.20,.24]]
tables[1]['citation_location']+='; selected contraction15-degree column also reviewed'
ports=[];rows=[]
for i,(a,b,length,family,frame,table) in enumerate(zip([start,mid],[mid,end],lengths,families,positions,tables)):
    data=dict(project_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'BSE3227:'+guid+':stage:'+str(i))),
        source='Separate staged construction candidate derived from saved transition '+guid+'; nominal clear sizes inherited. Intermediate section and redistributed straight ends are design assumptions, not product dimensions. Preserve original two external frames and total length; interaction and joints unresolved.',
        classification='assumed',wall_model='section_plane_offset',geometry_method='explicit_station_brep',
        start_section_m=a.tolist(),end_section_m=b.tolist(),section_offset_m=offset,
        start_length_m=straight,end_length_m=straight,upstream_angle_degrees=30.,transition_length_m=length,
        port_directions=dict(start='SINK',end='SOURCE'),
        placement=dict(source='Inherited original saved global frame with axial stage translation',origin_m=frame[:3,3].tolist(),rotation=frame[:3,:3].tolist()))
    request=OUT/('stage-'+str(i+1)+'.json');request.write_text(json.dumps(data,indent=2))
    native=OUT/('stage-'+str(i+1));result=author.run(request,native)
    saved=ifcopenshell.open(str(native/'transition.ifc'));fitting=saved.by_type('IfcDuctFitting')[0]
    geometry=calculate(fitting,'start','end');screen=family_check(family,geometry)
    assert screen['pass_check']
    quantities=dict(geometry['quantities'],inlet_to_outlet_area_ratio=math.prod(a)/math.prod(b))
    query=lookup(table,quantities);assert query['coefficient'] is not None
    owned={p.Name:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(fitting)}
    ports.append(owned)
    rows.append(dict(stage=i+1,family=family,start_section_m=a.tolist(),end_section_m=b.tolist(),
        total_length_m=author.total_length(data),native_checks=result['checks'],source_query=query,
        actual_included_angles_deg=[geometry['quantities'][n] for n in ['taper_width_angle_deg','taper_height_angle_deg']],
        ifc_sha256=result['ifc_sha256']))
oldports={p.Name:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(obj)}
assert np.allclose(oldports['start'],ports[0]['start'],atol=1e-8,rtol=0)
assert np.allclose(oldports['end'],ports[1]['end'],atol=1e-8,rtol=0)
assert np.allclose(ports[0]['end'][:3,3],ports[1]['start'][:3,3],atol=1e-8,rtol=0)
assert np.allclose(ports[0]['end'][:3,2],-ports[1]['start'][:3,2],atol=1e-9,rtol=0)
assert math.isclose(sum(r['total_length_m'] for r in rows),q['total_length_m'],abs_tol=1e-10)
assert sha(source)==before
record=dict(original_transition_guid=guid,source_ifc_sha256=before,stages=rows,
    original_total_length_m=q['total_length_m'],external_frames_preserved=True,new_internal_interface_count=1,
    source_families_match=True,original_network_modified=False,network_integrated=False,
    interaction_and_joint_losses_unknown=True,combined_pressure_Pa=None,pressure_budget_complete=False,design_accepted=False,
    inputs={str(Path(__file__)):sha(Path(__file__)),str(Path(author.__file__)):sha(Path(author.__file__))})
(OUT/'review.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:v for k,v in record.items() if k not in ['stages','inputs']},indent=2))
