import json,hashlib,math,uuid,itertools
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api,ifcopenshell.geom,ifcopenshell.validate
from ifcopenshell.util import placement,system
from bsa.stepped_cuff_geometry import build
from bsa.round_reducer_quantities import calculate as reducer
from bsa.duct_fitting_chain import value
from bsa.solid_clash import from_mesh
from outlet_native_batches import bounds,body,matrix
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');R=P/'07_Agent_Work/runs/logical-equipment-network';O=R/'stepped-cuff-joint-reviewed';O.mkdir(exist_ok=False);source=R/'open-lined-plenum-reviewed/Supply Air Open Plenum Candidate.ifc';m=ifcopenshell.open(str(source));old=ifcopenshell.open(str(source));I=json.loads((R/'integration.json').read_text());J=json.loads((R/'open-lined-plenum-reviewed/review.json').read_text());jby={r['plenum_guid']:r for r in J['records']};flow=json.loads((R/'pressure-interface-evidence/maximum/analysis.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guid=lambda n:ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,'bsa/stepped-cuff/'+n).hex);context=next(c for c in m.by_type('IfcGeometricRepresentationSubContext') if c.ContextIdentifier=='Body');records=[];shared=None;dims=None
for group in I['records']:
 j=jby[group['plenum_guid']]
 for out in group['outlets']:
  red=m.by_guid(out['reducer_guid']);r=reducer(red,flow['port_flows'][out['reducer_inlet_guid']]['flow_m3_s'],1.2);up=j['collar_OD'];down=float(r['inlet_diameter_m']+2*r['radial_gauge_m']);lap=.0254;film=.0008;wall=.0008;assert lap<min(j['projection'],r['inlet_collar_m']);current=(up,down,lap,wall,film)
  if shared is None:shared=build(m,context,upstream_outside_diameter_m=up,downstream_outside_diameter_m=down,half_length_m=lap,minimum_wall_m=wall,assumed_bondline_m=film);dims=current
  assert current==dims;frame=placement.get_local_placement(red.ObjectPlacement);portframe=placement.get_local_placement(m.by_guid(out['port_guid']).ObjectPlacement);assert np.allclose(frame[:3,3],portframe[:3,3],atol=1e-9) and np.allclose(frame[:3,1],portframe[:3,2],atol=1e-9)
  accessories=[]
  for kind,rep in zip(['SLEEVE','BONDLINE-PROXIES'],shared):
   obj=api.run('root.create_entity',m,ifc_class='IfcDiscreteAccessory',predefined_type='USERDEFINED',name=out['id']+'-'+kind);obj.GlobalId=guid(out['id']+'/'+kind);obj.ObjectType='Proposedsteppedoutersleeve' if kind=='SLEEVE' else 'Twonominalsealantbondlineproxies;notcuredproductgeometry';obj.Representation=rep;api.run('geometry.edit_object_placement',m,product=obj,matrix=frame,is_si=True);ps=api.run('pset.add_pset',m,product=obj,name='BSA_SteppedJointCandidate');api.run('pset.edit_pset',m,pset=ps,properties=dict(SourcePlenumGUID=group['plenum_guid'],SourceReducerGUID=red.GlobalId,HalfLength_m=lap,MinimumSleeveWall_m=wall,NominalBondline_m=film,DimensionClassification='Lap25.4mm/minwall0.8mm/bondline0.8mmaredesignassumptions;notmanufacturerapprovedjointdimensions',SealantMethodSource='Foster32-19PDSR0519NP,metalapplicationsnotUL181;candidateonly',SourcePDS_SHA256='fd9011c4b1c47891bc675371b94f6bfad3e4bc693b6be66ab4f9019118df87eb',BondlineScope='Nominalgeometryproxy;notderivedcuredthicknessfromwetfilm,dryingorshrinkage',MechanicalFastenersModelled=False,LeakageTestVerified=False,PressureClassVerified=False,ManufacturerAssemblyApproved=False));accessories.append(obj)
  m.create_entity('IfcRelConnectsWithRealizingElements',GlobalId=guid(out['id']+'/relationship'),RelatingElement=m.by_guid(group['plenum_guid']),RelatedElement=red,RealizingElements=accessories,ConnectionType='Candidate external stepped sleeve with two nominalbondlines;mechanicalfasteningandtestedsealunverified')
  records.append(dict(id=out['id'],plenum_guid=group['plenum_guid'],reducer_guid=red.GlobalId,sleeve_guid=accessories[0].GlobalId,bondline_guid=accessories[1].GlobalId,frame=frame.tolist(),upstream_OD_m=up,upstream_ID_m=up-2*j['metal'],downstream_OD_m=down,downstream_ID_m=r['inlet_diameter_m'],half_length_m=lap,bondline_m=film,min_wall_m=wall,source_reducer_collar_m=r['inlet_collar_m'],source_plenum_projection_m=j['projection']))
out=O/'Supply Air Stepped Joint Candidate.ifc';m.write(str(out));new=ifcopenshell.open(str(out));assert len(new.by_type('IfcElement'))==824 and len(new.by_type('IfcDistributionElement'))==604 and len(new.by_type('IfcDistributionPort'))==1287 and len(new.by_type('IfcRelConnectsPorts'))==603 and len(new.by_type('IfcRelConnectsWithRealizingElements'))==80
for obj in old.by_type('IfcElement'):
 q=new.by_guid(obj.GlobalId);assert value(q.Representation)==value(obj.Representation) and np.array_equal(placement.get_local_placement(q.ObjectPlacement),placement.get_local_placement(obj.ObjectPlacement))
for p in old.by_type('IfcDistributionPort'):
 q=new.by_guid(p.GlobalId);assert p.FlowDirection==q.FlowDirection and np.array_equal(placement.get_local_placement(p.ObjectPlacement),placement.get_local_placement(q.ObjectPlacement))
settings=ifcopenshell.geom.settings();settings.set('mesher-linear-deflection',1e-5);native=[]
a,b,lap,wall,film= dims[0]/2,dims[1]/2,*dims[2:];outer=b+film+wall
for kind,g,components,expected in [('sleeve',records[0]['sleeve_guid'],1,math.pi*lap*((outer**2-(a+film)**2)+(outer**2-(b+film)**2))),('bondlines',records[0]['bondline_guid'],2,math.pi*lap*(((a+film)**2-a*a)+((b+film)**2-b*b)))]:
 shape=ifcopenshell.geom.create_shape(settings,new.by_guid(g));v=np.array(shape.geometry.verts).reshape(-1,3);faces=np.array(shape.geometry.faces).reshape(-1,3);solid=from_mesh((v,faces));assert len(solid.decompose())==components and math.isclose(solid.volume(),expected,rel_tol=.005);native.append(dict(kind=kind,canonical_product_guid=g,native_connected_solids=components,native_material_volume_m3=solid.volume(),analytic_material_volume_m3=expected));np.savez_compressed(O/(kind+'-native.npz'),vertices=v,faces=faces)
# All shared instance frames and radial interval coverage are read from saved objects.
coverage=[];accessory_bounds=[];sourcebounds={o.GlobalId:bounds(body(o),matrix(o)) for o in new.by_type('IfcDistributionElement')}
for rec in records:
 for key in ['sleeve_guid','bondline_guid']:
  obj=new.by_guid(rec[key]);F=placement.get_local_placement(obj.ObjectPlacement);assert np.allclose(F,rec['frame'],atol=1e-10,rtol=0);assert np.allclose(F[:3,:3].T@F[:3,:3],np.eye(3),atol=1e-10) and np.linalg.det(F[:3,:3])>0;assert obj.Representation.id()==new.by_guid(records[0][key]).Representation.id();bb=[bounds(item,F) for item in obj.Representation.Representations[0].Items];accessory_bounds.append((rec['id'],obj.GlobalId,np.min([v[0] for v in bb],axis=0),np.max([v[1] for v in bb],axis=0)))
 # Saved source/native radii plus saved exact profiles must cover the full radial wall.
 sleeve=new.by_guid(rec['sleeve_guid']).Representation.Representations[0].Items[0];p=np.array([v.Coordinates for v in sleeve.SweptArea.OuterCurve.Points]);assert np.allclose(p,[(a+film,-lap),(outer,-lap),(outer,lap),(b+film,lap),(b+film,0),(a+film,0),(a+film,-lap)],rtol=0,atol=1e-12)
 seals=new.by_guid(rec['bondline_guid']).Representation.Representations[0].Items
 for side,radius,inner,seal in [('upstream',a,rec['upstream_ID_m']/2,seals[0]),('downstream',b,rec['downstream_ID_m']/2,seals[1])]:
  points=np.array([v.Coordinates for v in seal.SweptArea.OuterCurve.Points]);assert math.isclose(points[:,0].min(),radius,abs_tol=1e-12) and math.isclose(points[:,0].max(),radius+film,abs_tol=1e-12)
  intervals=[(inner,radius),(radius,radius+film),(radius+film,outer)];assert all(math.isclose(x[1],y[0],abs_tol=1e-12) for x,y in zip(intervals,intervals[1:]));coverage.append(dict(joint=rec['id'],side=side,nominal_radial_intervals_m=intervals,radial_gap_m=0.,mechanical_seal_verified=False))
possible=[]
owner={r['id']:{r['plenum_guid'],r['reducer_guid']} for r in records}
for i,(joint,g,lo,hi) in enumerate(accessory_bounds):
 for h,(bl,bh) in sourcebounds.items():
  if h not in owner[joint] and np.all(np.minimum(hi,bh)-np.maximum(lo,bl)>2e-5):possible.append([g,h])
 for other,h,bl,bh in accessory_bounds[i+1:]:
  if joint!=other and np.all(np.minimum(hi,bh)-np.maximum(lo,bl)>2e-5):possible.append([g,h])
assert not possible,possible[:5]
# Omit the bondline: the radial wall has a nonzero annular gap. Not leakage rate.
missing_bondline_gap=film;assert missing_bondline_gap>2e-5
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(new,logger,express_rules=True);assert not logger.statements,logger.statements[:3]
summary=dict(source_ifc_sha256=sha(source),ifc_sha256=sha(out),method_sha256=sha(A/'src/bsa/stepped_cuff_geometry.py'),sealant_PDS_sha256='fd9011c4b1c47891bc675371b94f6bfad3e4bc693b6be66ab4f9019118df87eb',elements=824,unchanged_source_elements=664,new_discrete_accessories=160,new_joint_relationships=80,distribution_elements=604,ports=1287,interfaces=603,all664source_representations_placements_unchanged=True,all1287port_frames_directions_unchanged=True,shared_whole_product_shapes=2,proper_rigid_instances_checked=160,native_canonical_checks=native,nominal_radial_sections_checked=160,unrelated_positive_AABB_overlap_candidates=0,related_contact_basis='Exactsavedradialintervals,lapwithincollarprojections;notmeshclashwaiveroractualjointtest',omitted_bondline_control_gap_m=missing_bondline_gap,schema_express_errors=0,records=records,nominal_radial_coverage=coverage,physical_joint_acceptance=False,sealant_cure_geometry_verified=False,mechanical_fasteners_modelled=False,pressure_verified=False,design_accepted=False,scope='Proposedcustomsteppedoutersleeveandtwobondlineproxies,notselectedmanufacturedconnectororverifiedairtightjoint.Onlynominalgeometryoccupancyandborepreservationarechecked.')
(O/'review.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['records','nominal_radial_coverage']}))
