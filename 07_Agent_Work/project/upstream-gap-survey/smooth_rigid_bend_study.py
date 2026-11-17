from pathlib import Path
import json,hashlib,math,copy,csv,inspect
import ifcopenshell,fluids.fittings,fluids.friction
from ifcopenshell.util import system
from bsa.smooth_round_bend import calculate
from bsa.duct_chain_analysis import boundary_paths
from bsa.source_pressure_ledger import calculate as ledger
A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=P/'07_Agent_Work/runs/logical-equipment-network';O=R/'smooth-rigid-bend-source-reviewed';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'Supply Air Logical Network.ifc';m=ifcopenshell.open(str(source));rows=[];terminal_rows=[];summaries={};key=lambda r:tuple(r[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])
for condition in ['maximum','minimum']:
 c=json.loads((R/'pressure-interface-evidence'/condition/'analysis.json').read_text());data=json.loads((R/'pressure-interface-evidence'/condition/'fitting-data.json').read_text());old=ledger(c,data);rho=c['air']['density_kg_m3'];mu=c['air']['viscosity_Pa_s'];by={}
 for req in data['data_requests']:
  obj=m.by_guid(req['product_guid'])
  if not obj.is_a('IfcDuctFitting') or obj.PredefinedType!='BEND' or not (obj.Name.startswith('SD-') and obj.Name.endswith(('/plan-bend','/terminal-bend'))):continue
  q=c['port_flows'][req['inlet_port_guid']]['flow_m3_s'];r=calculate(obj,q,rho,mu,construction_basis='smooth_rigid_candidate');by[key(req)]=r
 assert len(by)==160,[(m.by_guid(x['product_guid']).Name,x['predefined_type']) for x in data['data_requests'][-10:]]
 for st in c['straight_sections']:
  if st.get('construction_basis'):
   d=st['diameter_m'];v=st['flow_m3_s']/(math.pi*d*d/4);re=rho*v*d/mu;f=fluids.friction.friction_factor(Re=re,eD=0.,Method='Colebrook');st.update(straight_friction_Pa=f*st['length_m']/d*rho*v*v/2,calculation=dict(Re=re,Darcy_factor=f,velocity_m_s=v),construction_basis='Separate smooth rigid candidate,roughness0m;not installed flexible duct')
 c['boundary_paths']=boundary_paths(c['port_flows'],c['products'],c['interfaces'],c['straight_sections'],c['missing_fitting_path_losses'],c['boundary_ports'])
 for req in data['data_requests']:
  if key(req) not in by:continue
  r=by[key(req)];t=dict(**{k:req[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid']},status='calculated',coefficient=r['coefficient'],reference_port_guid=req['inlet_port_guid'],reference_velocity_pressure_Pa=r['reference_velocity_pressure_Pa'],signed_tabulated_contribution_Pa=r['conditional_bend_loss_Pa'],source_id='fluids131-rennels-smooth-bend',physical_applicability_verified=False,arc_friction_included=True)
  data['table_results'].append(t);req.update(recorded_table_result=t,status='conditional_numeric_value')
  rows.append(dict(condition=condition,product_guid=req['product_guid'],inlet_port_guid=req['inlet_port_guid'],outlet_port_guid=req['outlet_port_guid'],diameter_m=r['native_geometry']['inner_m'],radius_m=r['native_geometry']['radius_m'],angle_degrees=r['native_geometry']['angle_degrees'],design_flow_m3_s=r['flow_m3_s'],Reynolds=r['Reynolds'],Darcy_factor=r['Darcy_factor'],coefficient=r['coefficient'],conditional_bend_loss_Pa=r['conditional_bend_loss_Pa'],included_arc_friction_Pa=r['included_arc_friction_Pa'],physical_applicability_verified=False))
 tables={key(r):r for r in data['table_results']};data['boundary_paths']=[]
 for path in c['boundary_paths']:
  vals=[tables.get(key(s),{}).get('signed_tabulated_contribution_Pa') for s in path['steps'] if s['kind']=='fitting'];assert sum(v is None for v in vals)==3
  data['boundary_paths'].append(dict(inlet_port_guid=path['inlet_port_guid'],outlet_port_guid=path['outlet_port_guid'],known_straight_friction_Pa=path['known_straight_friction_Pa'],supplied_table_contribution_Pa=math.fsum(v for v in vals if v is not None),unresolved_fitting_path_count=3,tabulated_plus_separate_straight_Pa=None,complete_total_pressure_drop_Pa=None))
 c['branch_construction_override']=dict(construction='smooth rigid candidate only',roughness_m=0.,scope='Only160downstream straights and160round bends;mainroughness retained');c['straight_friction_subtotal_Pa']=math.fsum(s['straight_friction_Pa'] for s in c['straight_sections']);data.update(calculated_table_paths=354,unsupplied_table_paths=104,scope='Separate isolated smooth rigid branch study;not installed product or full pressure');data['sources']['fluids131-rennels-smooth-bend']=dict(version='1.3.1',license='MIT',source_url='https://fluids.readthedocs.io/fluids.fittings.html#fluids.fittings.bend_rounded',installed_module_sha256=sha(Path(inspect.getsourcefile(fluids.fittings))),citation='Rennels and Hudson 2012 via fluids implementation;original book not independently inspected');assert all(t['source_id'] in data['sources'] for t in data['table_results']);result=ledger(c,data);assert (result['conditional_numerical_path_count'],result['numerically_unresolved_fitting_path_count'])==(354,104)
 byold={p['outlet_port_guid']:p for p in old['outlet_paths']}
 for p in result['outlet_paths']:
  prior=byold[p['outlet_port_guid']];bs=[by[key(s)] for s in next(x for x in c['boundary_paths'] if x['outlet_port_guid']==p['outlet_port_guid'])['steps'] if s['kind']=='fitting' and key(s) in by];assert len(bs)==2
  assert math.isclose(p['conditional_signed_table_subtotal_Pa']-prior['conditional_signed_table_subtotal_Pa'],sum(b['conditional_bend_loss_Pa'] for b in bs),rel_tol=1e-11)
  terminal_rows.append(dict(condition=condition,terminal=c['port_flows'][p['outlet_port_guid']]['source_section'],terminal_port_guid=p['outlet_port_guid'],smooth_rigid_straight_partial_Pa=p['known_straight_friction_Pa'],conditional_component_partial_Pa=p['conditional_signed_table_subtotal_Pa'],two_bends_including_arc_friction_Pa=sum(b['conditional_bend_loss_Pa'] for b in bs),numeric_gaps=3,complete_pressure_Pa='Unknown'))
 folder=O/condition;folder.mkdir()
 for name,obj in [('analysis.json',c),('fitting-data.json',data),('pressure-ledger.json',result)]:(folder/name).write_text(json.dumps(obj,indent=2))
 summaries[condition]=dict(conditional_component_values=354,numerical_gaps=104,outlet_paths=80,gaps_per_outlet=3,bend_loss_range_Pa=[min(r['conditional_bend_loss_Pa'] for r in by.values()),max(r['conditional_bend_loss_Pa'] for r in by.values())])
# Actual geometry/input rejection controls and flow-law check.
obj=m.by_guid(rows[0]['product_guid']);n=0
for args in [dict(flow_m3_s=.1,density_kg_m3=1.2,viscosity_Pa_s=1.81e-5,construction_basis='corrugated_flex'),dict(flow_m3_s=True,density_kg_m3=1.2,viscosity_Pa_s=1.81e-5,construction_basis='smooth_rigid_candidate'),dict(flow_m3_s=1e-8,density_kg_m3=1.2,viscosity_Pa_s=1.81e-5,construction_basis='smooth_rigid_candidate')]:
 try:calculate(obj,**args)
 except ValueError:n+=1
 else:raise AssertionError('Unsafe study input accepted')
a=calculate(obj,.1,1.2,1.81e-5,construction_basis='smooth_rigid_candidate');b=calculate(obj,.2,1.2,3.62e-5,construction_basis='smooth_rigid_candidate');assert math.isclose(b['conditional_bend_loss_Pa'],4*a['conditional_bend_loss_Pa'],rel_tol=1e-12);assert a['conditional_bend_loss_Pa']>a['included_arc_friction_Pa']>0
summary=dict(source_ifc_sha256=sha(source),source_network='Existing logical network,geometry unchanged;separate smooth rigid pressure study',upstream_version='fluids1.3.1 MIT',upstream_source_url=a['source_url'],upstream_method_sha256=sha(Path(inspect.getsourcefile(fluids.fittings))),adapter_sha256=sha(A/'src/bsa/smooth_round_bend.py'),geometry_reader_sha256=sha(A/'src/bsa/round_bend_quantities.py'),cases=summaries,executed_bend_rows=len(rows),terminal_rows=len(terminal_rows),rejection_controls_passed=n,velocity_squared_control=True,arc_friction_included_once=True,roughness_m=0.,smooth_rigid_candidate_only=True,installed_flex_accepted=False,interaction_verified=False,main_pressure_accepted=False,complete_pressure_verified=False,remaining_numeric_gaps=dict(compound_main=4,VAV=20,plenum=80),scope='Isolated smooth-wall bend correlation,not interacting assembly or installed product;140equipment areas remain unknown,physical joints and diffuser discharge unresolved;no fan duty.')
(O/'review.json').write_text(json.dumps(summary,indent=2))
for name,rr in [('Smooth Rigid Bend Study.csv',rows),('Smooth Rigid Terminal Pressure Study.csv',terminal_rows)]:
 with (O/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
print(json.dumps(summary))
