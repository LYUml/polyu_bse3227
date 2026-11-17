import json,hashlib,math
from pathlib import Path
from collections import Counter
import numpy as np,ifcopenshell,ifcopenshell.api as api,ifcopenshell.geom,ifcopenshell.validate
from ifcopenshell.util import placement,system
from ifcopenshell.util.element import get_psets
import manifold3d as mm
from bsa.lined_plenum_geometry import build
from bsa.solid_clash import from_mesh
from bsa.duct_fitting_chain import value
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');R=P/'07_Agent_Work/runs/logical-equipment-network';O=R/'open-lined-plenum-reviewed';O.mkdir(exist_ok=False);source=R/'manufacturer-equipment-baseline/Supply Air Equipment Baseline.ifc';m=ifcopenshell.open(str(source));old=ifcopenshell.open(str(source));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();integration=json.loads((R/'integration.json').read_text());changed={r['plenum_guid'] for r in integration['records']};context=next(c for c in m.by_type('IfcGeometricRepresentationSubContext') if c.ContextIdentifier=='Body');records=[]
for row in integration['records']:
 obj=m.by_guid(row['plenum_guid']);ports=system.get_ports(obj);p=next(p for p in ports if p.FlowDirection=='SINK');pf=placement.get_local_placement(p.ObjectPlacement);x=-pf[:3,2];z=np.array([0.,0.,1.]);y=np.cross(z,x);F=np.eye(4);F[:3,:3]=np.column_stack((x,y,z));F[:3,3]=pf[:3,3];local=np.linalg.inv(placement.get_local_placement(obj.ObjectPlacement))@F;size=int(get_psets(m.by_guid(row['vav_guid']))['BSA_VAVCandidate']['NominalInlet_in']);W,H=np.array([16,15] if size==12 else [20,17.5])*.0254;L=36*.0254;t=.0008;liner=.0127;d=9.875*.0254;proj=3.375*.0254;stations=[(36-20.375)*.0254,(36-6.375)*.0254]
 for p in ports:
  f=placement.get_local_placement(p.ObjectPlacement);c=F[:3,:3].T@(f[:3,3]-F[:3,3]);n=F[:3,:3].T@f[:3,2]
  if p.FlowDirection=='SINK':assert np.allclose(c,0,atol=1e-9) and np.allclose(n,[-1,0,0],atol=1e-9)
  else:assert min(abs(c[0]-v) for v in stations)<1e-9 and abs(abs(c[1])-(W/2+proj))<1e-9 and abs(c[2])<1e-9 and np.allclose(n,[0,math.copysign(1,c[1]),0],atol=1e-9)
 for old_rep in list(obj.Representation.Representations):
  api.run('geometry.unassign_representation',m,product=obj,representation=old_rep);api.run('geometry.remove_representation',m,representation=old_rep)
 obj.Representation=build(m,context,local,width_m=float(W),height_m=float(H),length_m=L,metal_m=t,liner_m=liner,collar_outside_diameter_m=d,projection_m=proj,stations_m=stations);obj.ObjectType='Declared lined four-outlet open chamber candidate;combined occupied metal and liner volume,not manufacturer fabrication';ps=api.run('pset.add_pset',m,product=obj,name='BSA_OpenPlenumCandidate');api.run('pset.edit_pset',m,pset=ps,properties=dict(SourceCatalogueSHA256=integration['source_catalogue_sha256'],SourceLocator='A2-10/11 standardhalf-inchliner,J4outlets36in/DD9.875in',NominalMetalThickness_m=t,MetalThicknessBasis='Explicit0.8mmcandidate assumption;not verified conversionof22gauge',LinerThickness_m=liner,LinerBasis='Standardhalf-inchmanufacturerfeature;selectedcandidate,not installed selection',WidthHeightInterpretation='SourceW/Htreatedasoutsidecandidate envelope;manufacturer clearbore correspondence unverified',CollarLiningBasis='Candidateunlinedmetalcollar;actualinternalcollar/damperconstruction unresolved',BalancingDampersModelled=False,SlipDriveOverlapModelled=False,MaterialScope='Combined occupiedmetal+liner volume,not separate materialtakeoff',PressureLossVerified=False,InstalledProductVerified=False))
 for pn in ['BSA_EquipmentNetworkScope','BSA_JOutletCandidate']:
  psid=get_psets(obj)[pn]['id'];api.run('pset.edit_pset',m,pset=m.by_id(psid),properties={'GeometryScope':'Declaredopenlinedchambercandidate;manufacturerinternalsnotverified','RepresentationKind':'Combinedmetal+linermaterialCSGwall,notasolidcoordinationbox'})
 areas=[]
 for p in ports:
  area=float((W-2*(t+liner))*(H-2*(t+liner))) if p.FlowDirection=='SINK' else math.pi*(d/2-t)**2;areas.append(dict(port_guid=p.GlobalId,area_m2=area,kind='rectangular_chamber_entry' if p.FlowDirection=='SINK' else 'round_collar'))
  ps=api.run('pset.add_pset',m,product=p,name='BSA_CandidatePlenumBore');api.run('pset.edit_pset',m,pset=ps,properties=dict(CandidateClearArea_m2=area,AreaBasis='Derivedcandidategeometryonly;not manufacturerverifiedcleararea',ManufacturerClearAreaVerified=False,PhysicalJointVerified=False))
 records.append(dict(id=row['id'],plenum_guid=obj.GlobalId,nominal_size_in=size,frame=F.tolist(),W=float(W),H=float(H),L=L,metal=t,liner=liner,collar_OD=d,projection=proj,stations=stations,candidate_port_areas=areas))
out=O/'Supply Air Open Plenum Candidate.ifc';m.write(str(out));new=ifcopenshell.open(str(out));assert len(new.by_type('IfcElement'))==664 and len(new.by_type('IfcDistributionPort'))==1287 and len(new.by_type('IfcRelConnectsPorts'))==603
for obj in old.by_type('IfcElement'):
 q=new.by_guid(obj.GlobalId);assert np.array_equal(placement.get_local_placement(q.ObjectPlacement),placement.get_local_placement(obj.ObjectPlacement))
 if obj.GlobalId not in changed:assert value(q.Representation)==value(obj.Representation)
for p in old.by_type('IfcDistributionPort'):
 q=new.by_guid(p.GlobalId);assert q.FlowDirection==p.FlowDirection and np.array_equal(placement.get_local_placement(q.ObjectPlacement),placement.get_local_placement(p.ObjectPlacement))
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);settings.set('mesher-linear-deflection',1e-5);checks=[]
for rec in records:
 obj=new.by_guid(rec['plenum_guid']);shape=ifcopenshell.geom.create_shape(settings,obj);F=np.array(rec['frame']);v=(np.array(shape.geometry.verts).reshape(-1,3)-F[:3,3])@F[:3,:3];faces=np.array(shape.geometry.faces).reshape(-1,3);solid=from_mesh((v,faces));assert len(solid.decompose())==1;edges=Counter(tuple(sorted((int(a),int(b)))) for face in faces for a,b in zip(face,[face[1],face[2],face[0]]));euler=len(v)-len(edges)+len(faces);assert euler==-6 and all(n==2 for n in edges.values()),(rec['id'],euler)
 W,H,L,t,liner,d,proj=[rec[k] for k in ['W','H','L','metal','liner','collar_OD','projection']];a=t+liner;ri=d/2-t;expected=W*H*L-(W-2*a)*(H-2*a)*(L-a)+4*(math.pi*((d/2)**2-ri**2)*proj-math.pi*ri**2*a);assert math.isclose(solid.volume(),expected,rel_tol=.002,abs_tol=1e-10),(solid.volume(),expected)
 assert np.allclose([v.min(axis=0),v.max(axis=0)],[[0,-W/2-proj,-H/2],[L,W/2+proj,H/2]],rtol=0,atol=1e-7)
 # Connected independent five-mouth air probe: chamber plus four cylinders.
 probe=mm.Manifold.cube((L-a+.01,(W-2*a)*.9,(H-2*a)*.9)).translate((-.01,-(W-2*a)*.45,-(H-2*a)*.45))
 for x in rec['stations']:
  for sign in [-1,1]:
   cylinder=mm.Manifold.cylinder(W/2+proj+.01,ri*.9,ri*.9,64);M=np.array([[1,0,0,x],[0,0,sign,0],[0,-sign,0,0]],dtype=float);probe=probe+cylinder.transform(M)
 assert len(probe.decompose())==1;common=solid^probe;assert common.status()==mm.Error.NoError and abs(common.volume())<1e-10
 cap_areas=[]
 for ar in rec['candidate_port_areas']:
  p=new.by_guid(ar['port_guid']);pf=placement.get_local_placement(p.ObjectPlacement);point=F[:3,:3].T@(pf[:3,3]-F[:3,3]);normal=F[:3,:3].T@pf[:3,2];tri=v[faces];mask=np.max(abs((tri-point)@normal),axis=1)<1e-7
  if ar['kind']=='round_collar':mask &= np.max(abs(tri[:,:,0]-point[0]),axis=1)<d/2+1e-6
  triangles=tri[mask];area=float(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1).sum()/2);expected_area=W*H-ar['area_m2'] if ar['kind']=='rectangular_chamber_entry' else math.pi*((d/2)**2-ri**2);assert math.isclose(area,expected_area,rel_tol=.005,abs_tol=1e-10),(rec['id'],area,expected_area);cap_areas.append(dict(port_guid=p.GlobalId,native_material_cap_area_m2=area,analytic_material_cap_area_m2=expected_area))
 checks.append(dict(id=rec['id'],vertices=len(v),triangles=len(faces),one_connected_material=True,euler_characteristic=euler,native_material_volume_m3=solid.volume(),analytic_material_volume_m3=expected,connected_air_probe_material_overlap_m3=common.volume(),material_caps=cap_areas));print(rec['id'],'native open chamber verified',flush=True)
(O/'native-checkpoint.json').write_text(json.dumps(dict(records=records,checks=checks),indent=2))
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(new,logger,express_rules=True);assert not logger.statements,logger.statements[:3]
summary=dict(source_ifc_sha256=sha(source),ifc_sha256=sha(out),catalogue_sha256=integration['source_catalogue_sha256'],method_sha256=sha(A/'src/bsa/lined_plenum_geometry.py'),elements=664,ports=1287,interfaces=603,modified_plenums=20,unchanged_other_element_representations=644,all664element_placements_unchanged=True,all1287port_frames_directions_unchanged=True,native_plenum_meshes_checked=20,candidate_open_port_caps_checked=100,schema_express_errors=0,records=records,native_checks=checks,full_network_collision_verified=False,pressure_verified=False,physical_equipment_joints_verified=False,manufacturer_internal_geometry_verified=False,design_accepted=False,scope='Separatelinedchamberconstructioncandidate,combinedmetal+linervolume;0.8mmmetalassumption,half-inchlinerdefault,outsideW/Hinterpretation,unlinedcollars,no manualdamperblades orslipdriveoverlap.Originalsolidmodels preserved;no pressureorinstalledgeometryacceptance.')
(O/'review.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['records','native_checks']}))
