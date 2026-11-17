import copy,json,hashlib,math
from pathlib import Path
import ifcopenshell,ifcopenshell.geom,ifcopenshell.validate
from ifcopenshell.util import system
from bsa.source_network_analysis import prescribed_flows
from bsa.solid_clash import overlaps
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'constant-compound-core-candidate';p=R/'Supply Network.ifc';m=ifcopenshell.open(str(p));integration=json.loads((R/'integration.json').read_text());old=json.loads((B/'supported-transition-stages/flow-review.json').read_text());owned={o.GlobalId:[p.GlobalId for p in system.get_ports(o)] for o in m.by_type('IfcDistributionElement')};dirs={p.GlobalId:p.FlowDirection for p in m.by_type('IfcDistributionPort')};links=[(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in m.by_type('IfcRelConnectsPorts')];assert (len(owned),len(dirs),len(links))==(163,345,162);cases={}
for name,case in old['cases'].items():
 expected=copy.deepcopy(case['port_flows'])
 for row in integration['cases']:
  for g in row['new_internal_ports']:expected[g]=copy.deepcopy(expected[row['original_external_port_guid']])
 values=prescribed_flows(owned,dirs,links,expected);assert len(values)==345;assert all(math.isclose(values[g],row['flow_m3_s'],rel_tol=1e-12) for g,row in expected.items());cases[name]=dict(port_flows=expected,all345_source_demands_reconcile=True,inlet_m3_s=case['inlet_m3_s'],outlet_count=20)
(R/'flow-review.json').write_text(json.dumps(dict(cases=cases,original_requirement_ids=old['original_requirement_ids'],ifc_sha256=integration['ifc_sha256'],full_pressure_verified=False),indent=2))
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,logger,express_rules=True);assert not logger.statements;(R/'schema-review.json').write_text(json.dumps(dict(ifc_sha256=integration['ifc_sha256'],errors=0)))
s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);els=m.by_type('IfcDistributionElement');meshes={}
for e in els:
 shape=ifcopenshell.geom.create_shape(s,e);meshes[e.GlobalId]=(list(shape.geometry.verts),list(shape.geometry.faces))
f,u,n,c=overlaps(els,meshes,2e-5,1e-10,5000);report=dict(ifc_sha256=integration['ifc_sha256'],bodies=163,intersection_count=len(f),unverified=u,boolean_candidates=n,findings=f,scope='Physical duct bodies only; equipment casings and installation clearance excluded',design_accepted=False);(R/'intersection-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
