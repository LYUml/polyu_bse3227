"""Two sourced-family stages; preserve end flows and trim actual downstream straights."""
import copy,json,math,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_transition import run
from bsa.rectangular_tee_transitions import relative_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');O=B/'staged-main-transitions';O.mkdir(exist_ok=False)
GUIDS=['2S6vsh9WvK7QxoNkNqHEuL','0V2LoAkZ5G5gS9d5BbC$m4'];S=B/'sourced-inlet-network';source=S/'Supply Network.ifc';original=ifcopenshell.open(str(source));cases=[]
for index,guid in enumerate(GUIDS):
 obj=original.by_guid(guid);world=placement.get_local_placement(obj.ObjectPlacement);z=world[:3,2];pin=next(p for p in system.get_ports(obj) if p.FlowDirection=='SINK');pout=next(p for p in system.get_ports(obj) if p.FlowDirection=='SOURCE');oldend=placement.get_local_placement(pout.ObjectPlacement)[:3,3]
 folders=[];distance=0
 for stage,start,end in [(1,[.55,.35],[.5,.35]),(2,[.5,.35],[.4,.25])]:
  taper=max(abs(a-b) for a,b in zip(start,end))/(2*math.tan(math.radians(15)));origin=world[:3,3]+z*distance
  data=dict(project_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,guid+f'/stage{stage}')),source='Current saved native transition replacement; two explicit centred source families; design30degree maximum,50mmcollars; upstream interaction unverified',classification='assumed',placement=dict(source='Preserved saved native inlet frame and downstream axis',origin_m=origin.tolist(),rotation=world[:3,:3].tolist()),wall_model='section_plane_offset',start_section_m=start,end_section_m=end,section_offset_m=.0008,start_length_m=.05,end_length_m=.05,upstream_angle_degrees=30.,transition_length_m=taper,port_directions=dict(start='SINK',end='SOURCE'),geometry_method='explicit_station_brep')
  path=O/f'case{index+1}-stage{stage}.json';path.write_text(json.dumps(data,indent=2));folder=O/f'case{index+1}-stage{stage}';run(path,folder);folders.append(str(folder));distance+=.1+taper
 cases.append(dict(original_guid=guid,inlet_guid=pin.GlobalId,outlet_guid=pout.GlobalId,stage_folders=folders,frame=world.tolist(),old_end_m=oldend.tolist(),new_end_m=(world[:3,3]+z*distance).tolist(),additional_length_m=float(distance-np.linalg.norm(oldend-world[:3,3]))))

def revise(source,target):
 m=ifcopenshell.open(str(source));changes=[]
 for row in cases:
  obj=m.by_guid(row['original_guid']);owned=system.get_ports(obj);pin=m.by_guid(row['inlet_guid']);pout=m.by_guid(row['outlet_guid']);oldoutframe=placement.get_local_placement(pout.ObjectPlacement);oldpoint=oldoutframe[:3,3].copy()
  external=[r for r in (*pout.ConnectedTo,*pout.ConnectedFrom)];assert len(external)==1;r=external[0];peer=r.RelatedPort if r.RelatingPort==pout else r.RelatingPort;straight=system.get_port_element(peer);assert straight.is_a('IfcDuctSegment');pf={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(straight)}
  frame=placement.get_local_placement(straight.ObjectPlacement);pf[peer.GlobalId][:3,3]=row['new_end_m'];coords=[float((f[:3,3]-frame[:3,3])@frame[:3,2]) for f in pf.values()];depth=max(coords)-min(coords);assert depth>=.08;frame[:3,3]+=frame[:3,2]*min(coords);solid=straight.Representation.Representations[0].Items[0];olddepth=solid.Depth;solid.Depth=depth;straight.ObjectPlacement=relative_placement(m,frame,None)
  for p in system.get_ports(straight):p.ObjectPlacement=relative_placement(m,np.linalg.inv(frame)@pf[p.GlobalId],straight.ObjectPlacement)
  locals=[ifcopenshell.open(str(Path(f)/'transition.ifc')) for f in row['stage_folders']];fits=[l.by_type('IfcDuctFitting')[0] for l in locals];body=obj.Representation.Representations[0];body.Items=[m.add(fits[0].Representation.Representations[0].Items[0])]
  second=api.run('root.create_entity',m,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name='STAGED-MAIN-CONTRACTION');second.GlobalId=fits[1].GlobalId
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
  changes.append(dict(**row,second_guid=second.GlobalId,middleout_guid=middleout.GlobalId,middlein_guid=middlein.GlobalId,trimmed_straight_guid=straight.GlobalId,old_straight_depth_m=olddepth,new_straight_depth_m=depth))
 m.write(str(target));return changes
full=revise(source,O/'Supply Network.ifc');rect=revise(S/'trimmed-source.ifc',O/'Rectangular Source.ifc');assert all(a['second_guid']==b['second_guid'] for a,b in zip(full,rect));(O/'integration.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=full,body_count=131,ports=281,links=130,design_accepted=False),indent=2));print(json.dumps(full))
