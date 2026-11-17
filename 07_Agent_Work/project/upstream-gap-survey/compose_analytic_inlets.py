"""Reuse source-frame/port authoring with successful exact upstream CSG bodies."""
from pathlib import Path
HERE=Path(__file__).parent
text=(HERE/'author_compact_inlets.py').read_text()
text=text.replace("OUT=RUN/'local-candidates'", "OUT=RUN/'analytic-inlet-assemblies'")
text=text.replace("data=json.loads((RUN/'compact-meshes/mesh-review.json').read_text())",'''data=json.loads((RUN/'input.json').read_text());data['profiles']=[];keys={}
for row in data['cases']:
    key=tuple(row[k] for k in ['width_m','height_m','diameter_m','section_offset_m','taper_length_m','start_length_m','end_length_m'])
    if key not in keys:
        name='PROFILE-'+str(len(keys)+1);keys[key]=name
        data['profiles'].append(dict(profile=name,source_case=row['id']))
    row['profile']=keys[key]''')
text=text.replace("RUN/'kernel/kernel-review.json'", "RUN/'kernel-csg/kernel-review.json'")
start=text.index('maps={};profiles=[]');end=text.index('cases=[]',start)
text=text[:start]+'''maps={};profiles=[]
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
'''+text[end:]
text=text.replace("GeometrySource='CadQuery2.6.1/OCP7.8.1.1.post1;10micrometre absolute mesh target'", "GeometrySource='CadQuery2.6.1/OCP7.8.1.1.post1 exact loft BReps; IFC CSG wall'")
needle="    cases.append(dict(**row,guid=obj.GlobalId"
idx=text.index(needle)
extra='''    round_obj=api.run('root.create_entity',model,ifc_class='IfcDuctSegment',predefined_type='RIGIDSEGMENT',name=name+'-ROUND-LEAD');round_obj.GlobalId=guid(name+'/round-lead')
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
'''
text=text[:idx]+extra+text[idx:]
text=text.replace("OUT/'VAV Inlet Transitions.ifc'", "OUT/'VAV Inlet Assemblies.ifc'")
text=text.replace("components=20,ports=40", "components=40,ports=80,actual_links=20,exact_duplicate_vertex_entities_shared=duplicate_vertices")
text=text.replace("Finite source-bound transition candidates only; round lead and retained duct replacements not yet authored or connected", "Twenty actual finite transition-plus3Dround-lead assemblies; existing rectangular duct replacements and equipment connections not adopted")
text=text.replace("dict(components=20,ports=40,shared_profiles=len(profiles)", "dict(components=40,ports=80,actual_links=20,shared_profiles=len(profiles)")
target=HERE/'author_analytic_inlets.py';assert not target.exists();compile(text,str(target),'exec');target.write_text(text)
print(target)
