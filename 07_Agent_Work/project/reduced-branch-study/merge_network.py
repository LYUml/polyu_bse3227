"""Private verified network trial using unchanged public IFC/flow/table engines."""
import copy
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.util.element as element
import ifcopenshell.util.placement as placement
import ifcopenshell.util.system as system
from ifcopenshell.util.shape_builder import ShapeBuilder
from bsa import source_network_analysis as analysis
from bsa import source_compound_network as producer
from bsa import source_tee_network as inventory
from bsa import duct_fitting_data as tables
from bsa import duct_transition_quantities as transition
from bsa import duct_elbow_quantities as elbow
from bsa import unequal_rectangular_tee as author
from bsa import rectangular_tee as tee
from bsa.duct_fitting_chain import shape_hash

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'runs/source-network-analysis-native'
LOCAL = ROOT/'runs/reduced-branch-design-final'
BASIS = ROOT/'project/full-network-transition-study/basis.json'
OUT = ROOT/'runs/reduced-branch-network-reviewed'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
script_sha = sha(Path(__file__))
if OUT.exists():
    raise ValueError('Fresh output required')
analysis.verify(SOURCE)
original = json.loads((SOURCE/'analysis.json').read_text())
network_source = Path(original['source'])/'Supply Network.ifc'
before = sha(network_source)
study = json.loads((LOCAL/'study.json').read_text())
if any(sha(Path(p)) != h for p,h in study['inputs'].items()):
    raise ValueError('Local study source changed')
parent_tables=json.loads((ROOT/'runs/mcp-native-fitting-analysis/fitting-data.json').read_text())
canonical_ports={}
for request in parent_tables['data_requests']:
    for port in request['available_reference_ports']:
        key=port['port_guid']; value=(port['width_m'],port['height_m'])
        if key in canonical_ports and canonical_ports[key] != value:
            raise ValueError('Parent canonical port dimensions conflict')
        canonical_ports[key]=value
OUT.mkdir(parents=True)
model = ifcopenshell.open(str(network_source))
expected, _ = inventory.snapshot([network_source])
flow_bindings = {g:{k:r[k] for k in ('source_section','source_node','flow_m3_s','classification')} for g,r in original['port_flows'].items()}
revised = {}; removed = []; changes = []
for row in study['cases']:
    local = LOCAL/row['node']/'native'
    author.verify(local)
    data = json.loads((local/'result.json').read_text())['parameters']
    spec = data['tee']; guid = tee.stable_guid(spec,'IfcDuctFitting','RECTANGULAR-TEE')
    fitting = model.by_guid(guid)
    ports = {p.Name:p for p in system.get_ports(fitting)}
    branch = ports['branch']; branch_guid = branch.GlobalId
    links = [r for r in model.by_type('IfcRelConnectsPorts') if r.RelatingPort == branch]
    if len(links) != 1:
        raise ValueError('Unique original branch-to-transition required')
    start = links[0].RelatedPort; taper = system.get_port_element(start)
    if taper.PredefinedType != 'TRANSITION' or start.Name != 'start':
        raise ValueError('Original branch transition required')
    owned = system.get_ports(taper)
    if len(owned) != 2:
        raise ValueError('Two transition ports required')
    end = next(p for p in owned if p.Name=='end')
    outside = [r for r in model.by_type('IfcRelConnectsPorts') if r.RelatingPort == end]
    if len(outside) != 1:
        raise ValueError('Unique branch external peer required')
    peer = outside[0].RelatedPort
    frames = tee.port_frames(spec)
    if not np.allclose(placement.get_local_placement(end.ObjectPlacement), frames['branch'], atol=1e-8, rtol=0):
        raise ValueError('External branch frame changed')
    for name in ('main-a','main-b'):
        if not np.allclose(placement.get_local_placement(ports[name].ObjectPlacement),frames[name],atol=1e-8,rtol=0):
            raise ValueError('Original main frame changed')
    library = ifcopenshell.open(str(local/'unequal-tee.ifc')); replacement=library.by_guid(guid)
    context = fitting.Representation.Representations[0].ContextOfItems
    for representation in list(fitting.Representation.Representations):
        api.run('geometry.unassign_representation',model,product=fitting,representation=representation)
        api.run('geometry.remove_representation',model,representation=representation)
    body = element.copy_deep(model,replacement.Representation.Representations[0].Items[0])
    representation=ShapeBuilder(model).get_representation(context,[body],representation_type='CSG')
    api.run('geometry.assign_representation',model,product=fitting,representation=representation)
    updates = {k:v for k,v in element.get_psets(replacement)['BSA_DesignInputs'].items() if k!='id'}
    pset=next(r.RelatingPropertyDefinition for r in fitting.IsDefinedBy if r.RelatingPropertyDefinition.Name=='BSA_DesignInputs')
    api.run('pset.edit_pset',model,pset=pset,properties=copy.deepcopy(updates))
    expected['objects'][guid]['shape']=shape_hash(replacement)
    expected['objects'][guid]['properties']['BSA_DesignInputs'].update(updates)
    expected['ports'][branch_guid]['frame']=frames['branch'].tolist()
    api.run('geometry.edit_object_placement',model,product=branch,matrix=frames['branch'],is_si=True)
    taper_guid=taper.GlobalId; start_guid=start.GlobalId; end_guid=end.GlobalId; peer_guid=peer.GlobalId
    expected['links']=[tuple(pair) for pair in expected['links'] if start_guid not in pair and end_guid not in pair]+[(branch_guid,peer_guid)]
    for port in list(owned):
        expected['ports'].pop(port.GlobalId); flow_bindings.pop(port.GlobalId)
        api.run('root.remove_product',model,product=port)
    expected['objects'].pop(taper_guid)
    api.run('root.remove_product',model,product=taper)
    api.run('system.connect_port',model,port1=branch,port2=peer,direction='SOURCE')
    revised[guid]=data;removed.append(taper_guid)
    changes.append(dict(node=row['node'],tee_guid=guid,removed_transition_guid=taper_guid,branch_port_guid=branch_guid,external_peer_guid=peer_guid,external_frame_preserved=True))
expected['links']=sorted(set(map(tuple,expected['links'])))
target=OUT/'Supply Network.ifc';model.write(str(target))
checks=producer.inspect(target,expected)
saved=ifcopenshell.open(str(target))
case=analysis.calculate(saved,flow_bindings,original['air'])
case.update(air=original['air'],air_source_basis=original['air_source_basis'],original_requirement_ids=original['original_requirement_ids'],source=str(OUT),complete_network=False)
# Reuse the parent native canonical port dimensions only for unchanged bodies;
# revised branch dimensions are read from its inspected literal inner profile.
for obj in saved.by_type('IfcDistributionElement'):
    for p in system.get_ports(obj):
        current=case['port_flows'][p.GlobalId]
        if obj.GlobalId in revised and p.Name=='branch':
            profile=obj.Representation.Representations[0].Items[0].SecondOperand.SecondOperand.SweptArea
            width,height=profile.XDim,profile.YDim
        else:
            old=original['port_flows'][p.GlobalId]
            width,height=canonical_ports.get(p.GlobalId,(old['width_m'],old['height_m']))
        if not np.allclose([width,height],[current['width_m'],current['height_m']],atol=1e-8,rtol=0):
            raise ValueError('Actual material cap disagrees with literal/source section')
        v=current['flow_m3_s']/(width*height)
        current.update(width_m=width,height_m=height,actual_velocity_m_s=v,actual_velocity_pressure_Pa=case['air']['density_kg_m3']*v*v/2)
    product=next(x for x in case['products'] if x['guid']==obj.GlobalId)
    owned=system.get_ports(obj);incoming=next((p for p in owned if p.FlowDirection=='SINK'),None);outgoing=[p for p in owned if p.FlowDirection=='SOURCE']
    if obj.PredefinedType=='TRANSITION':
        product['transition_geometry']=transition.calculate(obj,incoming.Name,outgoing[0].Name)
    elif obj.PredefinedType=='BEND':
        product['elbow_geometry']=elbow.calculate(obj,incoming.Name,outgoing[0].Name,case['port_flows'][incoming.GlobalId]['flow_m3_s'],case['air'])
bound=json.loads(BASIS.read_text())
for source in bound['sources'].values():
    source['document']=str((BASIS.parent/source['document']).resolve())
bound['tables']=[x for x in bound['tables'] if x['product_guid'] not in removed]
for table in bound['tables']:
    guid=table['product_guid']
    if guid in revised:
        table['geometry_sha256']=shape_hash(saved.by_guid(guid))
        table['applicability_note']='Separate source-linked reduced-branch sharp90degree tee study. Actual native profile/cap/flow checks pass; source diagram and table conditions remain required. No extrapolation, whole-fitting friction/stations, adjacent-fitting interaction, product or physical installation acceptance.'
basis=OUT/'basis.json';basis.write_text(json.dumps(bound,indent=2))
prepared,pins=tables.prepare(basis)
loss=tables.calculate(saved,case,prepared)
if sha(network_source)!=before or sha(Path(__file__)) != script_sha:
    raise ValueError('Original network changed')
(OUT/'analysis.json').write_text(json.dumps(case,indent=2))
(OUT/'fitting-data.json').write_text(json.dumps(loss,indent=2))
report=dict(source_analysis=str(SOURCE),source_network_sha256=before,local_study_sha256=sha(LOCAL/'study.json'),changes=changes,native_checks=checks,
    products=len(case['products']),ports=len(case['port_flows']),outlets=len(case['boundary_paths']),flow_continuity_pass=case['flow_continuity_pass'],
    unique_fitting_paths=loss['unique_fitting_paths'],conditional_numerical_paths=loss['calculated_table_paths'],numerical_gaps=loss['unique_fitting_paths']-loss['calculated_table_paths'],
    inherited_source_requirements=len(case['original_requirement_ids']),original_network_modified=False,pressure_budget_complete=False,design_accepted=False,
    inputs={str(Path(__file__)):sha(Path(__file__)),str(SOURCE/'analysis.json'):sha(SOURCE/'analysis.json'),**pins},
    artifacts={p.name:sha(p) for p in (target,OUT/'analysis.json',OUT/'fitting-data.json')})
(OUT/'revision.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('changes','inputs','artifacts')},indent=2))
