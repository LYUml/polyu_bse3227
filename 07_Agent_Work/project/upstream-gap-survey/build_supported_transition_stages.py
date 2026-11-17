import copy,json,math,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_transition import run
from bsa.rectangular_tee_transitions import relative_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');O=B/'supported-transition-stages';O.mkdir(exist_ok=False);S=B/'compact-branch-stages';source=S/'Supply Network.ifc';original=ifcopenshell.open(str(source));requests=json.loads((S/'pressure-reviewed/maximum/fitting-data.json').read_text())['data_requests'];cases=[]
for request in requests:
 if request['status']!='source_data_required' or not request['transition_geometry']:continue
 guid=request['product_guid'];obj=original.by_guid(guid);world=placement.get_local_placement(obj.ObjectPlacement);z=world[:3,2];pin=original.by_guid(request['inlet_port_guid']);pout=original.by_guid(request['outlet_port_guid']);assert pin.Name=='start' and pout.Name=='end';oldend=placement.get_local_placement(pout.ObjectPlacement)[:3,3];a,b=[request['transition_geometry'][k] for k in ['inlet_section_m','outlet_section_m']];dw,dh=[v-w for v,w in zip(a,b)];assert min(dw,dh)>0 and abs(dw-dh)>1e-6;mid=[b[0]+dh,a[1]] if dw>dh else [a[0],b[1]+dw];folders=[];distance=0
 for stage,start,end in [(1,a,mid),(2,mid,b)]:
  taper=max(abs(u-v) for u,v in zip(start,end))/(2*math.tan(math.radians(22.5)));origin=world[:3,3]+z*distance;name='case'+str(len(cases)+1)+'-stage'+str(stage)
  data=dict(project_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,guid+'/supported-stages/'+str(stage))),source='Opt-in45degreeone-plane/equal-anglepyramidal native construction;sourceenddimensions and upstreamframepreserved;50mmcollars/gaugeassumed,physicalassemblyinteractionunverified',classification='assumed',placement=dict(source='Saved upstream native contraction frame',origin_m=origin.tolist(),rotation=world[:3,:3].tolist()),wall_model='section_plane_offset',start_section_m=start,end_section_m=end,section_offset_m=.0008,start_length_m=.05,end_length_m=.05,upstream_angle_degrees=45.,transition_length_m=taper,port_directions=dict(start='SINK',end='SOURCE'),geometry_method='explicit_station_brep');path=O/(name+'.json');path.write_text(json.dumps(data,indent=2));run(path,O/name);folders.append(str(O/name));distance+=.1+taper
 cases.append(dict(original_guid=guid,inlet_guid=pin.GlobalId,outlet_guid=pout.GlobalId,stage_folders=folders,frame=world.tolist(),old_end_m=oldend.tolist(),new_end_m=(world[:3,3]+z*distance).tolist(),additional_length_m=float(distance-np.linalg.norm(oldend-world[:3,3])),start_section_m=a,intermediate_section_m=mid,end_section_m=b))
assert len(cases)==9
def revise(source,target):
 m=ifcopenshell.open(str(source));changes=[]
 for row in cases:
  obj=m.by_guid(row['original_guid']);owned=system.get_ports(obj);pin=m.by_guid(row['inlet_guid']);pout=m.by_guid(row['outlet_guid']);oldoutframe=placement.get_local_placement(pout.ObjectPlacement);oldpoint=oldoutframe[:3,3].copy()
  external=[r for r in (*pout.ConnectedTo,*pout.ConnectedFrom)];assert len(external)==1;r=external[0];peer=r.RelatedPort if r.RelatingPort==pout else r.RelatingPort;straight=system.get_port_element(peer);assert straight.is_a('IfcDuctSegment');pf={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(straight)}
  frame=placement.get_local_placement(straight.ObjectPlacement);pf[peer.GlobalId][:3,3]=row['new_end_m'];coords=[float((f[:3,3]-frame[:3,3])@frame[:3,2]) for f in pf.values()];depth=max(coords)-min(coords);assert depth>=.08;frame[:3,3]+=frame[:3,2]*min(coords);solid=straight.Representation.Representations[0].Items[0];olddepth=solid.Depth;solid.Depth=depth;straight.ObjectPlacement=relative_placement(m,frame,None)
  for p in system.get_ports(straight):p.ObjectPlacement=relative_placement(m,np.linalg.inv(frame)@pf[p.GlobalId],straight.ObjectPlacement)
  locals=[ifcopenshell.open(str(Path(f)/'transition.ifc')) for f in row['stage_folders']];fits=[l.by_type('IfcDuctFitting')[0] for l in locals];body=obj.Representation.Representations[0];body.Items=[m.add(fits[0].Representation.Representations[0].Items[0])]
  second=api.run('root.create_entity',m,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name='STAGED-MAIN-CONTRACTION');second.GlobalId=fits[1].GlobalId;api.run('system.assign_system',m,products=[second],system=m.by_type('IfcDistributionSystem')[0])
  secondbody=m.create_entity('IfcShapeRepresentation',ContextOfItems=body.ContextOfItems,RepresentationIdentifier='Body',RepresentationType='CSG',Items=[m.add(fits[1].Representation.Representations[0].Items[0])]);api.run('geometry.assign_representation',m,product=second,representation=secondbody);second.ObjectPlacement=relative_placement(m,placement.get_local_placement(fits[1].ObjectPlacement),None)
  storey=m.by_type('IfcBuildingStorey')[0];m.create_entity('IfcRelContainedInSpatialStructure',GlobalId=ifcopenshell.guid.new(),RelatedElements=[second],RelatingStructure=storey)
  # Explicit ownership transfer preserves original external port/connection identity.
  nest=next(r for r in pout.Nests if r.is_a('IfcRelNests'));nest.RelatedObjects=[p for p in nest.RelatedObjects if p!=pout]
  middleout=api.run('system.add_port',m,element=obj);middleout.Name='end';middleout.FlowDirection='SOURCE';middleout.GlobalId=ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,row['original_guid']+'/middleout').hex)
  middlein=api.run('system.add_port',m,element=second);middlein.Name='start';middlein.FlowDirection='SINK';middlein.GlobalId=ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,row['original_guid']+'/middlein').hex)
  newnest=next(r for r in middlein.Nests if r.is_a('IfcRelNests'));newnest.RelatedObjects=[middlein,pout]
  for targetport,localfit,role,owner in [(middleout,fits[0],'end',obj),(middlein,fits[1],'start',second),(pout,fits[1],'end',second)]:
   lp=next(p for p in system.get_ports(localfit) if p.Name==role);world=placement.get_local_placement(lp.ObjectPlacement);targetport.ObjectPlacement=relative_placement(m,np.linalg.inv(placement.get_local_placement(owner.ObjectPlacement))@world,owner.ObjectPlacement);targetport.PredefinedType='DUCT';targetport.SystemType='VENTILATION'
  api.run('system.connect_port',m,port1=middleout,port2=middlein,direction='SOURCE')
  
  for product in [obj,second]:
   ps=api.run('pset.add_pset',m,product=product,name='BSA_TransitionStages');api.run('pset.edit_pset',m,pset=ps,properties=dict(OriginalTransitionGUID=row['original_guid'],DesignAngles_deg=45.,SourceScope='One-plane followed by equal-angle pyramidal contraction;tentative source and interaction unverified'))
  changes.append(dict(**row,second_guid=second.GlobalId,middleout_guid=middleout.GlobalId,middlein_guid=middlein.GlobalId,trimmed_straight_guid=straight.GlobalId,old_straight_depth_m=olddepth,new_straight_depth_m=depth))
 m.write(str(target));return changes
full=revise(source,O/'Supply Network.ifc');rect=revise(S/'Rectangular Source.ifc',O/'Rectangular Source.ifc');assert all(a['second_guid']==b['second_guid'] for a,b in zip(full,rect));(O/'integration.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=full,body_count=158,ports=335,links=157,design_accepted=False),indent=2));print(json.dumps(full))
