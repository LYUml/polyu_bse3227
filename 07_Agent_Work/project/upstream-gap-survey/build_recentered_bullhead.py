"""Source-area-sum bullhead candidate; preserves equipment boundaries."""
import json,math,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_transition import run
from bsa.rectangular_tee_transitions import relative_placement
from bsa.rectangular_tee_profiles import sections
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');S=B/'recentered-compact-branch-network';O=B/'recentered-bullhead-network';O.mkdir(exist_ok=False);GUID='2GbZoz5nfRsPMRMT$Zb04z';old=ifcopenshell.open(str(S/'Supply Network.ifc'));tee=old.by_guid(GUID);cases=[]
for p in system.get_ports(tee):
 if p.FlowDirection!='SOURCE':continue
 f=placement.get_local_placement(p.ObjectPlacement);name=p.Name;taper=(.65-.325)/(2*math.tan(math.radians(7.5)));spec=dict(project_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,p.GlobalId+'/area-sum-expansion')),source='Source5-33 area-sum candidate; common.65x.6,outlets.325x.6 each;15degree gradual expansions restore existing sections; engineering/product applicability remains unverified',classification='assumed',placement=dict(source='Actual saved J0 outward cap frame',origin_m=f[:3,3].tolist(),rotation=f[:3,:3].tolist()),wall_model='section_plane_offset',start_section_m=[.325,.6],end_section_m=[.65,.6],section_offset_m=.0008,start_length_m=.05,end_length_m=.05,upstream_angle_degrees=15.,transition_length_m=taper,port_directions=dict(start='SINK',end='SOURCE'),geometry_method='explicit_station_brep');path=O/(name+'.json');path.write_text(json.dumps(spec,indent=2));run(path,O/name);n=ifcopenshell.open(str(O/name/'transition.ifc'));obj=n.by_type('IfcDuctFitting')[0];ps={q.Name:q.GlobalId for q in system.get_ports(obj)};cases.append(dict(tee_guid=GUID,old_outlet_port_guid=p.GlobalId,folder=name,expander_guid=obj.GlobalId,expander_inlet_guid=ps['start'],expander_outlet_guid=ps['end'],additional_reach_m=.1+taper))
def revise(source,target):
 m=ifcopenshell.open(str(source));tee=m.by_guid(GUID);tee.Name='RECTANGULAR-BULLHEAD-TEE';wall=tee.Representation.Representations[0].Items[0]
 for union,g in [(wall.FirstOperand,.0008),(wall.SecondOperand,0.)]:
  profile=union.FirstOperand.SweptArea;union.FirstOperand.SweptArea=m.create_entity('IfcRectangleProfileDef',ProfileType='AREA',XDim=.325+2*g,YDim=profile.YDim)
 ps=api.run('pset.add_pset',m,product=tee,name='BSA_BullheadCandidate');api.run('pset.edit_pset',m,pset=ps,properties=dict(Source='2021PHVAC9supplement printed45Fitting5-33;candidate geometry,not physical product acceptance',CommonArea_m2=.39,EachOutletArea_m2=.195,AreaSumVerified=True))
 sections(tee,bullhead_area_sum=True);changes=[]
 for row in cases:
  p=m.by_guid(row['old_outlet_port_guid']);link=(*p.ConnectedTo,*p.ConnectedFrom)[0];peer=link.RelatedPort if link.RelatingPort==p else link.RelatingPort;chain=[];cursor=peer;seen=set();delta=placement.get_local_placement(p.ObjectPlacement)[:3,2]*row['additional_reach_m']
  while True:
   current=system.get_port_element(cursor);assert current.GlobalId not in seen;seen.add(current.GlobalId)
   if current.is_a('IfcDuctSegment'):straight=current;straightport=cursor;break
   assert current.is_a('IfcDuctFitting') and current.PredefinedType=='TRANSITION';owned=system.get_ports(current);assert len(owned)==2
   world=placement.get_local_placement(current.ObjectPlacement);frames={q.GlobalId:placement.get_local_placement(q.ObjectPlacement) for q in owned};chain.append((current,world,frames));out=next(q for q in owned if q.FlowDirection=='SOURCE');nextlink=(*out.ConnectedTo,*out.ConnectedFrom)[0];cursor=nextlink.RelatedPort if nextlink.RelatingPort==out else nextlink.RelatingPort
  assert len(chain)==2
  sf=placement.get_local_placement(straight.ObjectPlacement);sframes={q.GlobalId:placement.get_local_placement(q.ObjectPlacement) for q in system.get_ports(straight)};sframes[straightport.GlobalId][:3,3]+=delta;coords=[float((f[:3,3]-sf[:3,3])@sf[:3,2]) for f in sframes.values()];depth=max(coords)-min(coords);assert depth>=.08;olddepth=straight.Representation.Representations[0].Items[0].Depth;straight.Representation.Representations[0].Items[0].Depth=depth;sf[:3,3]+=sf[:3,2]*min(coords);straight.ObjectPlacement=relative_placement(m,sf,None)
  for q in system.get_ports(straight):q.ObjectPlacement=relative_placement(m,np.linalg.inv(sf)@sframes[q.GlobalId],straight.ObjectPlacement)
  for transition,world,frames in chain:
   world[:3,3]+=delta;transition.ObjectPlacement=relative_placement(m,world,None)
   for q in system.get_ports(transition):frames[q.GlobalId][:3,3]+=delta;q.ObjectPlacement=relative_placement(m,np.linalg.inv(world)@frames[q.GlobalId],transition.ObjectPlacement)
  local=ifcopenshell.open(str(O/row['folder']/'transition.ifc'));other=local.by_type('IfcDuctFitting')[0];obj=api.run('root.create_entity',m,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name='BULLHEAD-OUTLET-EXPANSION');obj.GlobalId=other.GlobalId;body=m.create_entity('IfcShapeRepresentation',ContextOfItems=tee.Representation.Representations[0].ContextOfItems,RepresentationIdentifier='Body',RepresentationType='CSG',Items=[m.add(other.Representation.Representations[0].Items[0])]);api.run('geometry.assign_representation',m,product=obj,representation=body);obj.ObjectPlacement=relative_placement(m,placement.get_local_placement(other.ObjectPlacement),None);m.create_entity('IfcRelContainedInSpatialStructure',GlobalId=ifcopenshell.guid.new(),RelatedElements=[obj],RelatingStructure=m.by_type('IfcBuildingStorey')[0]);api.run('system.assign_system',m,products=[obj],system=m.by_type('IfcDistributionSystem')[0]);ports={}
  for q in system.get_ports(other):
   port=api.run('system.add_port',m,element=obj);port.GlobalId=q.GlobalId;port.Name=q.Name;port.FlowDirection=q.FlowDirection;port.PredefinedType='DUCT';port.SystemType='VENTILATION';port.ObjectPlacement=relative_placement(m,np.linalg.inv(placement.get_local_placement(obj.ObjectPlacement))@placement.get_local_placement(q.ObjectPlacement),obj.ObjectPlacement);ports[port.Name]=port
  assert link.RelatingPort==p;link.RelatedPort=ports['start'];api.run('system.connect_port',m,port1=ports['end'],port2=peer,direction='SOURCE');changes.append(dict(**row,moved_transition_guids=[x[0].GlobalId for x in chain],trimmed_straight_guid=straight.GlobalId,old_depth_m=olddepth,new_depth_m=depth))
 m.write(str(target));return changes
full=revise(S/'Supply Network.ifc',O/'Supply Network.ifc');(O/'integration.json').write_text(json.dumps(dict(cases=full,bullhead_guid=GUID,body_count=116,ports=251,links=115,ifc_sha256=hashlib.sha256((O/'Supply Network.ifc').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((S/'Supply Network.ifc').read_bytes()).hexdigest(),design_accepted=False),indent=2));print(json.dumps(full))
