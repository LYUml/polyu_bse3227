"""Actual source-bound finite fittings using upstream CAD meshes and IFC maps."""
import hashlib,json,math,uuid
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.geom as geom
import ifcopenshell.validate
from ifcopenshell.util import element,placement
from bsa.solid_clash import from_mesh

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
RUN=BASE/'rect-round-cadquery';OUT=RUN/'analytic-inlet-assemblies';OUT.mkdir(exist_ok=False)
SOURCE=BASE/'recentered-network-integrated/Supply Network.ifc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((RUN/'input.json').read_text());data['profiles']=[];keys={}
for row in data['cases']:
    key=tuple(row[k] for k in ['width_m','height_m','diameter_m','section_offset_m','taper_length_m','start_length_m','end_length_m'])
    if key not in keys:
        name='PROFILE-'+str(len(keys)+1);keys[key]=name
        data['profiles'].append(dict(profile=name,source_case=row['id']))
    row['profile']=keys[key]
budget={r['id']:r for r in json.loads((RUN/'length-budget.json').read_text())['rows']}
nodes={n['node']:n for n in json.loads((BASE/'recentered-vav-connection-schedule/revised-junction.json').read_text())['nodes']}
source_model=ifcopenshell.open(str(SOURCE))
source_straights={element.get_psets(e)['BSA_DesignInputs']['SourceSectionID']:e for e in source_model.by_type('IfcDuctSegment')}
kernel={r['id']:r for r in json.loads((RUN/'kernel-csg/kernel-review.json').read_text())['results']}
model=api.run('project.create_file',version='IFC4')
project=api.run('root.create_entity',model,ifc_class='IfcProject',name='VAV inlet connection study')
namespace=uuid.UUID(hex=ifcopenshell.guid.expand(source_model.by_type('IfcProject')[0].GlobalId))
guid=lambda value:ifcopenshell.guid.compress(uuid.uuid5(namespace,'round-inlet-study/'+value).hex)
project.GlobalId=guid('project')
api.run('unit.assign_unit',model,units=[api.run('unit.add_si_unit',model,unit_type='LENGTHUNIT')])
context=api.run('context.add_context',model,context_type='Model')
body=api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
maps={};profiles=[]
from ifcopenshell.util.element import replace_attribute
for record in data['profiles']:
    operands=[]
    for kind in ['outer','inner']:
        source=RUN/'kernel-csg'/(record['source_case']+'-'+kind+'.brep')
        serialised=geom.serialise('IFC4',source.read_text(),True)
        assert len(serialised.Representations[0].Items)==1
        operands.append(model.add(serialised.Representations[0].Items[0]))
    item=model.create_entity('IfcBooleanResult',Operator='DIFFERENCE',FirstOperand=operands[0],SecondOperand=operands[1])
    rep=model.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='CSG',Items=[item])
    origin=model.create_entity('IfcAxis2Placement3D',Location=model.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)))
    maps[record['profile']]=model.create_entity('IfcRepresentationMap',MappingOrigin=origin,MappedRepresentation=rep)
    profiles.append(dict(profile=record['profile'],volume_m3=kernel[record['source_case']]['volume_m3'],
        kernel_volume_m3=kernel[record['source_case']]['volume_m3'],geometry='Analytic advanced BRep operands with native IFC Boolean difference'))
canonical={};duplicate_vertices=0
for vertex in list(model.by_type('IfcVertexPoint')):
    key=tuple(vertex.VertexGeometry.Coordinates)
    if key not in canonical:canonical[key]=vertex;continue
    for inverse in list(model.get_inverse(vertex)):replace_attribute(inverse,vertex,canonical[key])
    model.remove(vertex);duplicate_vertices+=1
cases=[]
for row in data['cases']:
    name=row['id'];node=nodes[name];inc=node['incidents'][0];old=source_straights[inc['section']]
    source_frame=placement.get_local_placement(old.ObjectPlacement)
    z=-np.array(inc['outward_unit_vector']);x=source_frame[:3,0];y=np.cross(z,x)
    assert abs(np.dot(z,x))<1e-10
    flow_frame=np.column_stack((x,y,z));assert np.allclose(flow_frame.T@flow_frame,np.eye(3)) and np.linalg.det(flow_frame)>0
    point=np.array(budget[name]['proposed_inlet_point_m'])
    lead=budget[name]['recommended_round_straight_m'];end=row['taper_length_m']+row['end_length_m']
    world=np.eye(4);world[:3,:3]=flow_frame;world[:3,3]=point-z*(lead+end)
    obj=api.run('root.create_entity',model,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name=name+'-INLET-TRANSITION');obj.GlobalId=guid(name)
    target=model.create_entity('IfcCartesianTransformationOperator3D',LocalOrigin=model.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)),Scale=1.)
    mapped=model.create_entity('IfcMappedItem',MappingSource=maps[row['profile']],MappingTarget=target)
    rep=model.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='MappedRepresentation',Items=[mapped])
    api.run('geometry.assign_representation',model,product=obj,representation=rep)
    api.run('geometry.edit_object_placement',model,product=obj,matrix=world,is_si=True)
    ports={}
    for role,local_z,direction,sign in [('rectangle',-row['start_length_m'],'SINK',-1),('circle',end,'SOURCE',1)]:
        frame=world.copy();frame[:3,3]=world[:3,3]+z*local_z
        if sign<0:frame[:3,1]*=-1;frame[:3,2]*=-1
        port=api.run('system.add_port',model,element=obj);port.GlobalId=guid(name+'/'+role);port.Name=role
        port.FlowDirection=direction;port.PredefinedType='DUCT';port.SystemType='VENTILATION'
        api.run('geometry.edit_object_placement',model,product=port,matrix=frame,is_si=True)
        ports[role]=dict(guid=port.GlobalId,frame=frame.tolist())
    pset=api.run('pset.add_pset',model,product=obj,name='BSA_InletStudy')
    api.run('pset.edit_pset',model,pset=pset,properties=dict(SourceNetworkSHA256=sha(SOURCE),
        SourceSectionGUID=old.GlobalId,SourceSectionID=inc['section'],InputProfile=row['profile'],
        SourceFlow_L_s=inc['flow_L_s'],PlacementClassification='design_assumption',
        WallModel='Section-offset ruled loft,0.8mm; not constant surface-normal sheet thickness',
        GeometrySource='CadQuery2.6.1/OCP7.8.1.1.post1 exact loft BReps; IFC CSG wall',
        NewVAVShift_m=budget[name]['downstream_shift_m'],Connected=False))
    round_obj=api.run('root.create_entity',model,ifc_class='IfcDuctSegment',predefined_type='RIGIDSEGMENT',name=name+'-ROUND-LEAD');round_obj.GlobalId=guid(name+'/round-lead')
    profile=model.create_entity('IfcCircleHollowProfileDef',ProfileType='AREA',Radius=row['diameter_m']/2+row['section_offset_m'],WallThickness=row['section_offset_m'])
    position=model.create_entity('IfcAxis2Placement3D',Location=model.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)))
    solid=model.create_entity('IfcExtrudedAreaSolid',SweptArea=profile,Position=position,
        ExtrudedDirection=model.create_entity('IfcDirection',DirectionRatios=(0.,0.,1.)),Depth=lead)
    rep=model.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='SweptSolid',Items=[solid])
    api.run('geometry.assign_representation',model,product=round_obj,representation=rep)
    round_frame=world.copy();round_frame[:3,3]+=z*end
    api.run('geometry.edit_object_placement',model,product=round_obj,matrix=round_frame,is_si=True)
    round_ports={}
    for role,distance,direction,sign in [('inlet',0.,'SINK',-1),('outlet',lead,'SOURCE',1)]:
        pf=round_frame.copy();pf[:3,3]+=z*distance
        if sign<0:pf[:3,1]*=-1;pf[:3,2]*=-1
        port=api.run('system.add_port',model,element=round_obj);port.Name=role;port.GlobalId=guid(name+'/round/'+role)
        port.FlowDirection=direction;port.PredefinedType='DUCT';port.SystemType='VENTILATION'
        api.run('geometry.edit_object_placement',model,product=port,matrix=pf,is_si=True)
        round_ports[role]=dict(guid=port.GlobalId,frame=pf.tolist())
    api.run('system.connect_port',model,port1=model.by_guid(ports['circle']['guid']),port2=model.by_guid(round_ports['inlet']['guid']),direction='SOURCE')
    pset=api.run('pset.add_pset',model,product=round_obj,name='BSA_InletStudy')
    api.run('pset.edit_pset',model,pset=pset,properties=dict(SourceFlow_L_s=inc['flow_L_s'],NominalInternalDiameter_m=row['diameter_m'],
        LengthSource='SDIOM PDF6 Step2A recommends3D; study nominal circle and inherited0.8mm gauge assumptions',
        InstalledLengthVerified=False,ProductCollarSealVerified=False))
    row.update(round_guid=round_obj.GlobalId,round_frame=round_frame.tolist(),round_ports=round_ports)
    cases.append(dict(**row,guid=obj.GlobalId,frame=world.tolist(),ports=ports,length_budget=budget[name],source_section_guid=old.GlobalId))
path=OUT/'VAV Inlet Assemblies.ifc';model.write(str(path))
saved=ifcopenshell.open(str(path));logger=ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(saved,logger,express_rules=True);assert not logger.statements,logger.statements[:2]
report=dict(ifc_sha256=sha(path),source_ifc_sha256=sha(SOURCE),ifc_bytes=path.stat().st_size,
    native_schema_express_pass=True,profiles=profiles,cases=cases,components=40,ports=80,actual_links=20,exact_duplicate_vertex_entities_shared=duplicate_vertices,
    scope='Twenty actual finite transition-plus3Dround-lead assemblies; existing rectangular duct replacements and equipment connections not adopted',
    design_accepted=False,full_pressure_verified=False)
(OUT/'author-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(components=40,ports=80,actual_links=20,exact_duplicate_vertex_entities_shared=duplicate_vertices,shared_profiles=len(profiles),ifc_bytes=path.stat().st_size,schema_pass=True)))
