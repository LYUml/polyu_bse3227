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
RUN=BASE/'rect-round-cadquery';OUT=RUN/'local-candidates';OUT.mkdir(exist_ok=False)
SOURCE=BASE/'recentered-network-integrated/Supply Network.ifc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((RUN/'compact-meshes/mesh-review.json').read_text())
budget={r['id']:r for r in json.loads((RUN/'length-budget.json').read_text())['rows']}
nodes={n['node']:n for n in json.loads((BASE/'recentered-vav-connection-schedule/revised-junction.json').read_text())['nodes']}
source_model=ifcopenshell.open(str(SOURCE))
source_straights={element.get_psets(e)['BSA_DesignInputs']['SourceSectionID']:e for e in source_model.by_type('IfcDuctSegment')}
kernel={r['id']:r for r in json.loads((RUN/'kernel/kernel-review.json').read_text())['results']}
model=api.run('project.create_file',version='IFC4')
project=api.run('root.create_entity',model,ifc_class='IfcProject',name='VAV inlet connection study')
namespace=uuid.UUID(hex=ifcopenshell.guid.expand(source_model.by_type('IfcProject')[0].GlobalId))
guid=lambda value:ifcopenshell.guid.compress(uuid.uuid5(namespace,'round-inlet-study/'+value).hex)
project.GlobalId=guid('project')
api.run('unit.assign_unit',model,units=[api.run('unit.add_si_unit',model,unit_type='LENGTHUNIT')])
context=api.run('context.add_context',model,context_type='Model')
body=api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
maps={};profiles=[]
for record in data['profiles']:
    path=RUN/'compact-meshes'/(record['profile']+'.npz');assert sha(path)==record['mesh_sha256']
    raw=np.load(path);original=raw['vertices']
    mesh=trimesh.Trimesh(vertices=original,faces=raw['faces'],process=False)
    # Merge seam duplicates only within a measured1e-10m computational budget;
    # do not flip faces, fill holes, simplify or repair shape geometry.
    mesh.merge_vertices(digits_vertex=10)
    displacement=float(cKDTree(mesh.vertices).query(original)[0].max())
    assert displacement<=1e-10 and mesh.is_watertight and mesh.is_winding_consistent
    solid=from_mesh((mesh.vertices,mesh.faces));volume=solid.volume()
    assert math.isclose(volume,kernel[record['source_case']]['volume_m3'],rel_tol=.002)
    coordinates=model.create_entity('IfcCartesianPointList3D',CoordList=np.asarray(mesh.vertices).tolist())
    item=model.create_entity('IfcTriangulatedFaceSet',Coordinates=coordinates,Closed=True,
        CoordIndex=(np.asarray(mesh.faces)+1).tolist())
    rep=model.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='Tessellation',Items=[item])
    origin=model.create_entity('IfcAxis2Placement3D',Location=model.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)))
    maps[record['profile']]=model.create_entity('IfcRepresentationMap',MappingOrigin=origin,MappedRepresentation=rep)
    profiles.append(dict(profile=record['profile'],volume_m3=volume,
        kernel_volume_m3=kernel[record['source_case']]['volume_m3'],seam_merge_maximum_displacement_m=displacement,
        vertices=len(mesh.vertices),faces=len(mesh.faces)))
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
        GeometrySource='CadQuery2.6.1/OCP7.8.1.1.post1;10micrometre absolute mesh target',
        NewVAVShift_m=budget[name]['downstream_shift_m'],Connected=False))
    cases.append(dict(**row,guid=obj.GlobalId,frame=world.tolist(),ports=ports,length_budget=budget[name],source_section_guid=old.GlobalId))
path=OUT/'VAV Inlet Transitions.ifc';model.write(str(path))
saved=ifcopenshell.open(str(path));logger=ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(saved,logger,express_rules=True);assert not logger.statements,logger.statements[:2]
report=dict(ifc_sha256=sha(path),source_ifc_sha256=sha(SOURCE),ifc_bytes=path.stat().st_size,
    native_schema_express_pass=True,profiles=profiles,cases=cases,components=20,ports=40,
    scope='Finite source-bound transition candidates only; round lead and retained duct replacements not yet authored or connected',
    design_accepted=False,full_pressure_verified=False)
(OUT/'author-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(components=20,ports=40,shared_profiles=len(profiles),ifc_bytes=path.stat().st_size,schema_pass=True)))
