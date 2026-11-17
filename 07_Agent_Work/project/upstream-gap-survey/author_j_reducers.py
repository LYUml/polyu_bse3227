"""Native analytic round reducer candidates, explicit nominal clear-bore assumptions."""
import json,math,hashlib,uuid
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api,ifcopenshell.geom as geom
from bsa.solid_clash import from_mesh
from bsa.circular_geometry import configure
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');S=B/'j-outlet-candidate';O=B/'j-outlet-reducer-candidate-verified';O.mkdir(exist_ok=False)
source=S/'geometry/model.ifc';m=ifcopenshell.open(str(source));before={e.id():str(e) for e in m};x=json.loads((S/'review.json').read_text());context=m.by_id(10);storey=m.by_type('IfcBuildingStorey')[0]
D1=.254;D2=.2032;g=.0008;c=.05;angle=15.;L=(D1-D2)/2/math.tan(math.radians(angle/2));total=L+2*c
points=[(D1/2+g,0.),(D1/2+g,c),(D2/2+g,c+L),(D2/2+g,total),(D2/2,total),(D2/2,c+L),(D1/2,c),(D1/2,0.)]
curve=m.create_entity('IfcPolyline',Points=[m.create_entity('IfcCartesianPoint',Coordinates=p) for p in [*points,points[0]]]);profile=m.create_entity('IfcArbitraryClosedProfileDef',ProfileType='AREA',OuterCurve=curve)
position=m.create_entity('IfcAxis2Placement3D',Location=m.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)));axis=m.create_entity('IfcAxis1Placement',Location=m.create_entity('IfcCartesianPoint',Coordinates=(0.,0.,0.)),Axis=m.create_entity('IfcDirection',DirectionRatios=(0.,1.,0.)))
solid=m.create_entity('IfcRevolvedAreaSolid',SweptArea=profile,Position=position,Axis=axis,Angle=2*math.pi)
ns=uuid.UUID('a2c31124-6fae-4e59-85c6-bc75ca3c51e8');uid=lambda s:ifcopenshell.guid.compress(uuid.uuid5(ns,s).hex)
records=[]
for group in x['records']:
 for p in group['ports']:
  name=p['id']+'-REDUCER';obj=api.run('root.create_entity',m,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name=name);obj.GlobalId=uid(name)
  rep=m.create_entity('IfcShapeRepresentation',ContextOfItems=context,RepresentationIdentifier='Body',RepresentationType='SweptSolid',Items=[solid]);api.run('geometry.assign_representation',m,product=obj,representation=rep)
  z=np.array(p['direction']);radial=np.array([0.,0.,1.]);normal=np.cross(radial,z);frame=np.eye(4);frame[:3,:3]=np.column_stack([radial,z,normal]);frame[:3,3]=p['point_m'];assert abs(np.linalg.det(frame[:3,:3])-1)<1e-9
  api.run('geometry.edit_object_placement',m,product=obj,matrix=frame,is_si=True);m.create_entity('IfcRelContainedInSpatialStructure',GlobalId=uid(name+'containment'),RelatedElements=[obj],RelatingStructure=storey)
  ports=[]
  for role,distance,direction in [('inlet',0.,'SINK'),('outlet',total,'SOURCE')]:
   port=api.run('system.add_port',m,element=obj);port.Name=role;port.GlobalId=uid(name+role);port.FlowDirection=direction;port.SystemType='AIRCONDITIONING';pf=np.eye(4);axisdir=-z if role=='inlet' else z;pf[:3,:3]=np.column_stack([radial,np.cross(axisdir,radial),axisdir]);pf[:3,3]=np.array(p['point_m'])+z*distance;api.run('geometry.edit_object_placement',m,product=port,matrix=pf,is_si=True);ports.append(dict(role=role,guid=port.GlobalId,point_m=pf[:3,3].tolist()))
  ps=api.run('pset.add_pset',m,product=obj,name='BSA_ReducerCandidate');api.run('pset.edit_pset',m,pset=ps,properties=dict(VAVID=group['id'],NominalUpstream_in=10,NominalDownstream_in=8,ClearBoreBasis='Nominal duct IDs assumed; collar sheet gauge and insertion compatibility unverified',RadialGauge_m=g,IncludedAngle_deg=angle,DimensionsClassification='Design targets, not manufacturer reducer ratings',PhysicalApplicabilityVerified=False))
  records.append(dict(id=name,product_guid=obj.GlobalId,ports=ports,plenum_outlet_id=p['id'],vav=group['id'],new_branch_origin_m=ports[1]['point_m']))
assert all(str(m.by_id(i))==text for i,text in before.items());path=O/'Candidate Round Reducers.ifc';m.write(str(path));saved=ifcopenshell.open(str(path));settings=geom.settings();configure(settings);settings.set(settings.USE_WORLD_COORDS,True)
volume=math.pi*((D1/2+g)**2-(D1/2)**2)*c+math.pi*((D2/2+g)**2-(D2/2)**2)*c+math.pi*L/3*((D1/2+g)**2+(D1/2+g)*(D2/2+g)+(D2/2+g)**2-(D1/2)**2-D1*D2/4-(D2/2)**2)
errors=[]
for r in records:
 obj=saved.by_guid(r['product_guid']);shape=geom.create_shape(settings,obj);s=from_mesh((shape.geometry.verts,shape.geometry.faces));errors.append(abs(s.volume()/volume-1))
assert max(errors)<.001
out=dict(source_ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),ifc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reducer_count=80,new_ports=160,original229element_model_records_unchanged=True,design_dimensions=dict(inlet_clear_bore_m=D1,outlet_clear_bore_m=D2,radial_gauge_m=g,collar_each_m=c,taper_included_angle_deg=angle,taper_m=L,total_m=total),all80positive_closed_solids=True,maximum_mesh_volume_relative_error=max(errors),analytic_wall_volume_each_m3=volume,records=records,source_collar_external_dimensions_m=dict(J_outlet=9.875*.0254,diffuser8_neck=7.875*.0254),source_1400_dimensions_sha256=hashlib.sha256((S/'1400-dimensions.pdf').read_bytes()).hexdigest(),collar_seam_or_insertion_verified=False,clashes_verified=False,pressure_verified=False,design_accepted=False)
(O/'review.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'}))



