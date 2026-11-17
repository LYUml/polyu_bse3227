import json,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api,ifcopenshell.validate
from ifcopenshell.util import placement,system
from bsa.rectangular_tee_transitions import relative_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');O=B/'recentered-transition-stage-candidates';source=B/'recentered-network-integrated/Supply Network.ifc';cases=json.loads((O/'review.json').read_text())['cases']
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

target=O/'Supply Network.ifc';assert not target.exists();changes=revise(source,target)
m=ifcopenshell.open(str(target));logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,logger,express_rules=True)
counts=dict(bodies=len(m.by_type('IfcDistributionElement')),ports=len(m.by_type('IfcDistributionPort')),links=len(m.by_type('IfcRelConnectsPorts')))
(O/'integration.json').write_text(json.dumps(dict(changes=changes,counts=counts,schema_issues=logger.statements,design_accepted=False),indent=2,default=str));print(json.dumps(dict(counts=counts,schema_issues=len(logger.statements))))
