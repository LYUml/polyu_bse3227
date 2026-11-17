"""Reconcile unchanged source demands through the actual revised saved tree."""
import copy,hashlib,json,math
from pathlib import Path
import ifcopenshell
from ifcopenshell.util import system
from bsa.source_network_analysis import prescribed_flows

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
RUN=BASE/'compact-branch-stages';path=RUN/'Supply Network.ifc';model=ifcopenshell.open(str(path))
source=BASE/'constant-height-tee-network/flow-review.json';old=json.loads(source.read_text())
owned={o.GlobalId:[p.GlobalId for p in system.get_ports(o)] for o in model.by_type('IfcDistributionElement')}
directions={p.GlobalId:p.FlowDirection for p in model.by_type('IfcDistributionPort')}
links=[(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in model.by_type('IfcRelConnectsPorts')]
results={}
for condition in ['maximum','minimum']:
    expected=copy.deepcopy(old['cases'][condition]['port_flows'])
    
    for row in json.loads((RUN/'integration.json').read_text())['cases']:
        for g in [ps[role] for ps in row['stage_ports'] for role in ['start','end']]:expected[g]=copy.deepcopy(expected[row['branch_port_guid']])
    values=prescribed_flows(owned,directions,links,expected)
    connected={g for pair in links for g in pair}
    ins=[g for g in values if g not in connected and directions[g]=='SINK'];outs=[g for g in values if g not in connected and directions[g]=='SOURCE']
    assert len(ins)==1 and len(outs)==20 and len(values)==317
    assert math.isclose(values[ins[0]],math.fsum(values[g] for g in outs),rel_tol=1e-12)
    results[condition]=dict(port_flows=expected,inlet_m3_s=values[ins[0]],outlet_count=20,all317source_demands_reconcile=True)
output=RUN/'flow-review.json';assert not output.exists()
output.write_text(json.dumps(dict(cases=results,original_requirement_ids=old['original_requirement_ids'],
    ifc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_flow_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    flow_prescription_not_passive_balance=True,full_pressure_verified=False),indent=2))
print('Both317port actual source-flow cases reconcile')
