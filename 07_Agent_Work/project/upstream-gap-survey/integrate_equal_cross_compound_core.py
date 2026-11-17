import json,uuid,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_tee_transitions import relative_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');O=B/'equal-cross-compound-core-candidate';S=B/'supported-transition-stages';review=json.loads((O/'review.json').read_text());newports=[]
def revise(source,target):
 m=ifcopenshell.open(str(source));obj=m.by_guid(review['source_guid']);local=ifcopenshell.open(str(O/'core/junction.ifc'));core=local.by_type('IfcDuctFitting')[0];body=obj.Representation.Representations[0];body.Items=[m.add(core.Representation.Representations[0].Items[0])];oldports={p.Name:p for p in system.get_ports(obj)};coreframes={p.Name:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(core)};mapping=[]
 for row in review['cases']:
  old=oldports[row['port']];ext=(*old.ConnectedTo,*old.ConnectedFrom)[0];peer=ext.RelatedPort if ext.RelatingPort==old else ext.RelatingPort;straight=system.get_port_element(peer);assert straight.GlobalId==row['adjacent_straight_guid'];sf=placement.get_local_placement(straight.ObjectPlacement);pframes={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(straight)};pframes[peer.GlobalId][:3,3]=row['new_external_point_m'];coords=[float((f[:3,3]-sf[:3,3])@sf[:3,2]) for f in pframes.values()];depth=max(coords)-min(coords);assert abs(depth-row['remaining_straight_length_m'])<1e-9;sf[:3,3]+=sf[:3,2]*min(coords);straight.ObjectPlacement=relative_placement(m,sf,None);straight.Representation.Representations[0].Items[0].Depth=depth
  for p in system.get_ports(straight):p.ObjectPlacement=relative_placement(m,np.linalg.inv(sf)@pframes[p.GlobalId],straight.ObjectPlacement)
  nest=old.Nests[0];nest.RelatedObjects=[p for p in nest.RelatedObjects if p!=old]
  cp=api.run('system.add_port',m,element=obj);cp.Name=row['port'];cp.GlobalId=ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,old.GlobalId+'/equalcrosscore').hex);cp.FlowDirection='SOURCE';cp.PredefinedType='DUCT';cp.SystemType='VENTILATION';cp.ObjectPlacement=relative_placement(m,np.linalg.inv(placement.get_local_placement(obj.ObjectPlacement))@coreframes[row['port']],obj.ObjectPlacement);last=cp;added=[cp.GlobalId]
  for i,folder in enumerate(row['stage_folders']):
   l=ifcopenshell.open(str(Path(folder)/'transition.ifc'));lo=l.by_type('IfcDuctFitting')[0];fit=api.run('root.create_entity',m,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name='COMPOUND-CORE-EXTERNAL-TRANSITION');fit.GlobalId=lo.GlobalId;fit.ObjectPlacement=relative_placement(m,placement.get_local_placement(lo.ObjectPlacement),None);rep=m.create_entity('IfcShapeRepresentation',ContextOfItems=body.ContextOfItems,RepresentationIdentifier='Body',RepresentationType='CSG',Items=[m.add(lo.Representation.Representations[0].Items[0])]);api.run('geometry.assign_representation',m,product=fit,representation=rep);api.run('system.assign_system',m,products=[fit],system=m.by_type('IfcDistributionSystem')[0]);m.create_entity('IfcRelContainedInSpatialStructure',GlobalId=ifcopenshell.guid.new(),RelatedElements=[fit],RelatingStructure=m.by_type('IfcBuildingStorey')[0]);ps={}
   for lp in system.get_ports(lo):
    final=lp.Name=='end' and i==len(row['stage_folders'])-1
    if final:
     p=old;m.create_entity('IfcRelNests',GlobalId=ifcopenshell.guid.new(),RelatingObject=fit,RelatedObjects=[p])
    else:p=api.run('system.add_port',m,element=fit);p.GlobalId=lp.GlobalId;added.append(p.GlobalId)
    p.Name=lp.Name;p.FlowDirection=lp.FlowDirection;p.PredefinedType='DUCT';p.SystemType='VENTILATION';p.ObjectPlacement=relative_placement(m,np.linalg.inv(placement.get_local_placement(fit.ObjectPlacement))@placement.get_local_placement(lp.ObjectPlacement),fit.ObjectPlacement);ps[p.Name]=p
   api.run('system.connect_port',m,port1=last,port2=ps['start'],direction='SOURCE');last=ps['end']
  mapping.append(dict(original_external_port_guid=old.GlobalId,new_internal_ports=added))
 ps=api.run('pset.add_pset',m,product=obj,name='BSA_ConstantCompoundCore');api.run('pset.edit_pset',m,pset=ps,properties=dict(Source='Separate assumed constant1350x900core;three constant-height branches and five external transitions',CoefficientVerification=False,NetworkPressureAcceptance=False));m.write(str(target));assert len(m.by_type('IfcDistributionElement'))== (164 if 'Supply' in source.name else 124);return mapping
full=revise(S/'Supply Network.ifc',O/'Supply Network.ifc');sub=revise(S/'Rectangular Source.ifc',O/'Rectangular Source.ifc');assert full==sub;record=dict(source_sha256=review['source_ifc_sha256'],ifc_sha256=hashlib.sha256((O/'Supply Network.ifc').read_bytes()).hexdigest(),cases=full,bodies=164,ports=347,links=163,full_pressure_accepted=False,design_accepted=False);(O/'integration.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))

