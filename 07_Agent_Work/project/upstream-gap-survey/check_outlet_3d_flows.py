import json,hashlib,math,copy
from pathlib import Path
import ifcopenshell
from ifcopenshell.util import system
from bsa.source_network_analysis import prescribed_flows
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';p=R/'Supply and Three Dimensional Outlet Candidate.ifc';m=ifcopenshell.open(str(p));review=json.loads((R/'review.json').read_text());old=json.loads((B/'equal-cross-compound-core-candidate/flow-review.json').read_text());inlets={r['id']:r['source_port_guid'] for r in json.loads((B/'equal-cross-compound-core-candidate/equipment-space/sync-review.json').read_text())['rows']};owned={o.GlobalId:[p.GlobalId for p in system.get_ports(o)] for o in m.by_type('IfcDistributionElement')};dirs={p.GlobalId:p.FlowDirection for p in m.by_type('IfcDistributionPort')};links=[(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in m.by_type('IfcRelConnectsPorts')];assert (len(owned),len(dirs),len(links))==(564,1147,483);parent={k:k for k in owned}
def find(x):
 while parent[x]!=x:x=parent[x]
 return x
for a,b in links:
 x,y=[system.get_port_element(m.by_guid(g)).GlobalId for g in [a,b]];rx,ry=find(x),find(y);assert rx!=ry;parent[rx]=ry
components=len({find(g) for g in parent});assert components==81;cases={}
for name in ['maximum','minimum']:
 expected=copy.deepcopy(old['cases'][name]['port_flows']);groups={k:[] for k in inlets}
 for route in review['records']:
  q=route['source_flows'][name]['flow_m3_s'];groups[route['vav']].append(q);objects=[m.by_guid(route['reducer_guid'])]+[m.by_guid(p['guid']) for p in route['pieces']]
  for obj in objects:
   for port in system.get_ports(obj):expected[port.GlobalId]=dict(source_section=route['terminal'],source_node=route['vav'],flow_m3_s=q,classification='Inherited terminal allocation,not measured flow')
 values=prescribed_flows(owned,dirs,links,expected);assert len(values)==1147
 for vav,qs in groups.items():assert len(qs)==4 and math.isclose(math.fsum(qs),values[inlets[vav]],rel_tol=1e-12)
 cases[name]=dict(all1147_source_demands_reconciled=True,twenty_vav_group_totals_match_main_inlet_boundary_flows=True,branch_flow_total_m3_s=math.fsum(route['source_flows'][name]['flow_m3_s'] for route in review['records']),do_not_sum_main_and_disconnected_branch_source_totals=True)
report=dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),distribution_bodies=564,ports=1147,interfaces=483,connected_components=81,topology='One164body main tree plus80fivebody downstream chains;equipment/plenum internal airway connections NOT represented',cases=cases,continuous_full_airflow_system=False,full_pressure_verified=False,design_accepted=False);(R/'flow-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
