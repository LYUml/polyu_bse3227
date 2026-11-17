"""Compose verified rectangular engine with native circular spans and real graph."""
import copy,hashlib,json,math
from pathlib import Path
import ifcopenshell
from ifcopenshell.util import system
from fluids.friction import friction_factor
from bsa import duct_chain_analysis as paths,duct_fitting_data as fitting,source_pressure_ledger as ledger,source_tee_network as inventory

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
RUN=BASE/'reduced-cross-network';OUT=RUN/'pressure-reviewed';OUT.mkdir(exist_ok=False)
IFC=RUN/'Supply Network.ifc';model=ifcopenshell.open(str(IFC))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cap=json.loads((RUN/'native-cap-review.json').read_text());assert cap['ifc_sha256']==sha(IFC)
flow=json.loads((RUN/'flow-review.json').read_text())
local=json.loads((BASE/'rect-round-sourced-design/analytic-inlet-assemblies/author-review.json').read_text())
full,_=inventory.snapshot([IFC]);sub,_=inventory.snapshot([RUN/'Rectangular Source.ifc'])
for key in ['objects','ports']:
    assert all(full[key][g]==row for g,row in sub[key].items())
basis,pins=fitting.prepare(RUN/'rectangular-pressure/basis.json')
summary={}
for condition in ['maximum','minimum']:
    source=RUN/'rectangular-pressure'/condition/'analysis.json'
    case=json.loads(source.read_text());air=case['air'];rho=air['density_kg_m3']
    for row in local['cases']:
        old_guid=row['source_section_guid'];original_ports=system.get_ports(model.by_guid(old_guid))
        source_profile=model.by_guid(old_guid).Representation.Representations[0].Items[0].SweptArea
        w,h=source_profile.XDim-2*source_profile.WallThickness,source_profile.YDim-2*source_profile.WallThickness
        round_obj=model.by_guid(row['round_guid']);solid=round_obj.Representation.Representations[0].Items[0]
        D=2*(solid.SweptArea.Radius-solid.SweptArea.WallThickness);L=solid.Depth
        for owner,ports in [(row['guid'],row['ports']),(row['round_guid'],row['round_ports'])]:
            qin=qout=0.
            for role,p in ports.items():
                g=p['guid'];q=flow['cases'][condition]['port_flows'][g]['flow_m3_s']
                rectangular=owner==row['guid'] and role=='rectangle'
                area=w*h if rectangular else math.pi*D**2/4
                direction=model.by_guid(g).FlowDirection
                record=dict(**flow['cases'][condition]['port_flows'][g],owner_guid=owner,direction=direction,
                    graph_derived_flow_m3_s=q,section_type='rectangular' if rectangular else 'circular',
                    actual_area_m2=area,actual_velocity_m_s=q/area,actual_velocity_pressure_Pa=rho*(q/area)**2/2)
                if rectangular:record.update(width_m=w,height_m=h)
                else:record['diameter_m']=D
                case['port_flows'][g]=record
                if direction=='SINK':qin+=q
                else:qout+=q
            assert math.isclose(qin,qout,rel_tol=1e-12)
            case['products'].append(dict(guid=owner,ifc_class=model.by_guid(owner).is_a(),incoming_flow_m3_s=qin,outgoing_flow_m3_s=qout,continuity_pass=True))
        q=case['port_flows'][row['round_ports']['inlet']['guid']]['flow_m3_s'];v=q/(math.pi*D**2/4)
        Re=rho*v*D/air['viscosity_Pa_s'];assert Re>4000
        f=friction_factor(Re=Re,eD=air['roughness_m']/D)
        case['straight_sections'].append(dict(guid=row['round_guid'],section_type='circular',length_m=L,
            diameter_m=D,flow_m3_s=q,calculation=dict(Re=Re,Darcy_factor=f,velocity_m_s=v),straight_friction_Pa=f*L/D*rho*v*v/2))
        case['missing_fitting_path_losses'].append(dict(product_guid=row['guid'],ifc_class='IfcDuctFitting',predefined_type='TRANSITION',
            inlet_port_guid=row['ports']['rectangle']['guid'],outlet_port_guid=row['ports']['circle']['guid'],coefficient=None,
            required_basis=['Applicable rectangle-to-circle ruled-loft source and actual reference station','Published support, whole-body friction and physical joint applicability']))
    interfaces=[];connected=set()
    for link in model.by_type('IfcRelConnectsPorts'):
        a,b=link.RelatingPort.GlobalId,link.RelatedPort.GlobalId
        qa,qb=[case['port_flows'][g]['flow_m3_s'] for g in [a,b]];assert math.isclose(qa,qb,rel_tol=1e-12)
        interfaces.append(dict(source_port=a,sink_port=b,flow_m3_s=qa,continuity_pass=True));connected.update([a,b])
    case['interfaces']=interfaces;case['boundary_ports']=[g for g in case['port_flows'] if g not in connected]
    case['boundary_paths']=paths.boundary_paths(case['port_flows'],case['products'],interfaces,case['straight_sections'],case['missing_fitting_path_losses'],case['boundary_ports'])
    case['straight_friction_subtotal_Pa']=math.fsum(r['straight_friction_Pa'] for r in case['straight_sections'])
    assert len(case['port_flows'])==291 and len(case['products'])==136 and len(case['straight_sections'])==65
    assert len(case['missing_fitting_path_losses'])==90 and len(case['boundary_paths'])==20
    result=fitting.calculate(model,case,basis);result['original_requirement_ids']=case['original_requirement_ids']
    from adopt_cross_rect_round_source import apply
    result=apply(model,case,result,condition)
    pressure=ledger.calculate(case,result)
    assert pressure['numerically_unresolved_fitting_path_count']==24
    folder=OUT/condition;folder.mkdir()
    for name,data in [('analysis.json',case),('fitting-data.json',result),('pressure-ledger.json',pressure)]:
        (folder/name).write_text(json.dumps(data,indent=2))
    summary[condition]=dict(ports=291,straight_sections=65,fitting_paths=90,conditional_values=result['calculated_table_paths'],numerical_gaps=24,
        outlet_paths=20,inlet_m3_s=flow['cases'][condition]['inlet_m3_s'])
(OUT/'review.json').write_text(json.dumps(dict(ifc_sha256=sha(IFC),cases=summary,source_subgraph_exactly_matches_saved_full_model=True,
    full_pressure_verified=False,design_accepted=False),indent=2))
print(json.dumps(summary,indent=2))
