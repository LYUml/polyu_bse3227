import json,math,hashlib,copy
from pathlib import Path
import ifcopenshell,ifcopenshell.validate
from ifcopenshell.util import system
from bsa.source_network_analysis import prescribed_flows
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'logical-equipment-network';model_path=R/'Supply Air Logical Network.ifc';m=ifcopenshell.open(str(model_path));integration=json.loads((R/'integration.json').read_text());main=json.loads((B/'equal-cross-compound-core-candidate/flow-review.json').read_text());branches=json.loads((B/'three-dimensional-outlet-candidate/review.json').read_text())['records'];owned={o.GlobalId:[p.GlobalId for p in system.get_ports(o)] for o in m.by_type('IfcDistributionElement')};directions={p.GlobalId:p.FlowDirection for p in m.by_type('IfcDistributionPort')};links=[(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in m.by_type('IfcRelConnectsPorts')];occupied={g for pair in links for g in pair};results={}
for condition in ['maximum','minimum']:
 expected=copy.deepcopy(main['cases'][condition]['port_flows'])
 for branch in branches:
  q=branch['source_flows'][condition]['flow_m3_s']
  for guid in [branch['reducer_guid']]+[p['guid'] for p in branch['pieces']]:
   for p in system.get_ports(m.by_guid(guid)):expected[p.GlobalId]=dict(source_section=branch['terminal'],source_node=branch['vav'],flow_m3_s=q,classification='Inherited preliminary terminal demand,not measured')
 for row in integration['records']:
  total=expected[row['main_outlet_guid']]['flow_m3_s']
  for g in [row['vav_inlet_guid'],row['vav_outlet_guid'],row['plenum_inlet_guid']]:expected[g]=dict(source_section=row['id'],source_node=row['id'],flow_m3_s=total,classification='Source-positioned equipment flow,candidate assumption')
  for outlet in row['outlets']:expected[outlet['port_guid']]=copy.deepcopy(expected[outlet['reducer_inlet_guid']])
 values=prescribed_flows(owned,directions,links,expected);assert len(values)==1287;roots=[g for g in values if g not in occupied and directions[g]=='SINK'];leaves=[g for g in values if g not in occupied and directions[g]=='SOURCE'];assert len(roots)==1 and len(leaves)==80;assert math.isclose(values[roots[0]],math.fsum(values[g] for g in leaves),rel_tol=1e-12)
 # One acyclic component,not merely a balanced forest.
 owners={g:o for o,ps in owned.items() for g in ps};parent={g:g for g in owned}
 def find(g):
  while parent[g]!=g:g=parent[g]
  return g
 for a,b in links:
  u,v=find(owners[a]),find(owners[b]);assert u!=v;parent[u]=v
 assert len({find(g) for g in owned})==1
 results[condition]=dict(port_flows=expected,boundary_inlet_guid=roots[0],boundary_outlet_guids=sorted(leaves),inlet_m3_s=values[roots[0]],outlet_m3_s=math.fsum(values[g] for g in leaves),outlets=80,connected_components=1,all1287_source_demands_reconcile=True)
(R/'flow-review.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),cases=results,original_requirement_ids=main['original_requirement_ids'],logical_tree_verified=True,physical_airway_continuity_verified=False,full_pressure_verified=False),indent=2));print('Both1287portcases:oneinlet/80outlets/oneacyclictree',flush=True)
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,logger,express_rules=True);assert not logger.statements;(R/'schema-review.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),schema_express_errors=0),indent=2));print('IFC schema EXPRESS pass')

