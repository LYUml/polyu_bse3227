import copy,json,math,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_transition import run
from bsa.rectangular_tee_transitions import relative_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');O=B/'recentered-transition-stage-candidates';O.mkdir(exist_ok=False);S=B/'recentered-network-integrated';source=S/'Supply Network.ifc';original=ifcopenshell.open(str(source));fitting_data=json.loads((S/'pressure/maximum/fitting-data.json').read_text());bad={r['product_guid'] for r in fitting_data['table_results'] if r.get('reason')=='declared transition family not met'};requests=[r for r in fitting_data['data_requests'] if r['product_guid'] in bad];cases=[]

for request in requests:
 if request['status']!='native_condition_failed' or not request['transition_geometry']:continue
 guid=request['product_guid'];obj=original.by_guid(guid);world=placement.get_local_placement(obj.ObjectPlacement);z=world[:3,2];pin=original.by_guid(request['inlet_port_guid']);pout=original.by_guid(request['outlet_port_guid']);assert pin.Name=='start' and pout.Name=='end';oldend=placement.get_local_placement(pout.ObjectPlacement)[:3,3];a,b=[request['transition_geometry'][k] for k in ['inlet_section_m','outlet_section_m']];dw,dh=[v-w for v,w in zip(a,b)];assert min(dw,dh)>0 and abs(dw-dh)>1e-6;mid=[b[0]+dh,a[1]] if dw>dh else [a[0],b[1]+dw];folders=[];distance=0
 for stage,start,end in [(1,a,mid),(2,mid,b)]:
  taper=max(abs(u-v) for u,v in zip(start,end))/(2*math.tan(math.radians(22.5)));origin=world[:3,3]+z*distance;name='case'+str(len(cases)+1)+'-stage'+str(stage)
  data=dict(project_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,guid+'/supported-stages/'+str(stage))),source='Opt-in45degreeone-plane/equal-anglepyramidal native construction;sourceenddimensions and upstreamframepreserved;50mmcollars/gaugeassumed,physicalassemblyinteractionunverified',classification='assumed',placement=dict(source='Saved upstream native contraction frame',origin_m=origin.tolist(),rotation=world[:3,:3].tolist()),wall_model='section_plane_offset',start_section_m=start,end_section_m=end,section_offset_m=.0008,start_length_m=.05,end_length_m=.05,upstream_angle_degrees=45.,transition_length_m=taper,port_directions=dict(start='SINK',end='SOURCE'),geometry_method='explicit_station_brep');path=O/(name+'.json');path.write_text(json.dumps(data,indent=2));run(path,O/name);folders.append(str(O/name));distance+=.1+taper
 cases.append(dict(original_guid=guid,inlet_guid=pin.GlobalId,outlet_guid=pout.GlobalId,stage_folders=folders,frame=world.tolist(),old_end_m=oldend.tolist(),new_end_m=(world[:3,3]+z*distance).tolist(),additional_length_m=float(distance-np.linalg.norm(oldend-world[:3,3])),start_section_m=a,intermediate_section_m=mid,end_section_m=b))

assert len(cases)==2
from bsa.duct_transition_quantities import calculate,family_check
checks=[]
for row in cases:
 stage_checks=[]
 for n,folder in enumerate(row['stage_folders']):
  model=ifcopenshell.open(str(Path(folder)/'transition.ifc'));obj=model.by_type('IfcDuctFitting')[0];geometry=calculate(obj,'start','end');family=['centred_one_plane','centred_equal_angle_pyramidal'][n];check=family_check(family,geometry);assert check['pass_check'];stage_checks.append(dict(family=family,geometry=geometry,family_check=check))
 assert np.linalg.norm(np.array(row['new_end_m'])-row['old_end_m'])<.002
 checks.append(dict(original_guid=row['original_guid'],stages=stage_checks))
review=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=cases,native_stage_checks=checks,authored_components=4,source_family_geometry_pass=True,network_integrated=False,pressure_recalculated=False,design_accepted=False)
(O/'review.json').write_text(json.dumps(review,indent=2));print(json.dumps(dict(components=4,cases=2,additional_lengths_m=[r['additional_length_m'] for r in cases],native_source_families_pass=True,network_integrated=False)))
