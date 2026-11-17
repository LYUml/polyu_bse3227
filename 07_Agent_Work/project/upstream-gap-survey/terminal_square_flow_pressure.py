import json,subprocess,hashlib,math,csv
from pathlib import Path
from bsa.manufacturer_adpi import catalogue
from bsa.terminal_pressure_curve import calculate,square_law_rounding_band
from bsa.source_pressure_ledger import calculate as ledger
A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';R=B/'logical-equipment-network';O=R/'terminal-square-flow-pressure';O.mkdir(exist_ok=False);source=P/'07_Agent_Work/project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf';table=catalogue(source)['8'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Upstream report verifier reads existing PDF bytes; no desktop invocation.
T=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit');cli=T/'.venv/Scripts/k-select.exe';native=[]
for name,pdf,q in [('maximum',P/'05_Calculations/k-select sd-01 maximum.pdf',280),('minimum',T/'local/auto-112-v2/performance.pdf',112)]:
 before=sha(pdf);raw=subprocess.check_output([str(cli),'report-verify',str(pdf),'--airflow',str(q),'--neck-in','8','--module','24x24'],text=True,encoding='utf-8');v=json.loads(raw);(O/(name+'-native-verification.json')).write_text(json.dumps(v,indent=2));assert v['ok'] and all(v['checks'].values()) and before==sha(pdf);report=v['report'];selected=report['selected'];assert selected['airflow_cfm']==q;flow=q*.4719474432;result=calculate(table,flow);display=selected['pressure_in_wc'];interval=[(display-.005)*249.08891,(display+.005)*249.08891];native.append(dict(condition=name,effective_CFM=q,effective_flow_L_s=flow,source_pdf_sha256=before,native_display_in_wc=display,assumed_display_interval_Pa=interval,squared_flow_catalogue_total_pressure_Pa=result['total_pressure_Pa'],linear_flow_catalogue_total_pressure_Pa=result['linear_flow_comparison_total_pressure_Pa'],squared_flow_matches_display=interval[0]<=result['total_pressure_Pa']<=interval[1],linear_flow_matches_display=interval[0]<=result['linear_flow_comparison_total_pressure_Pa']<=interval[1],software_accuracy_verified=False,native_software_rerun=False))
assert all(r['squared_flow_matches_display'] for r in native) and not native[1]['linear_flow_matches_display']
# Hold each internal catalogue row out and predict it from its neighbours.
held=[]
for i in range(1,len(table)-1):
 q=table[i]['flow_L_s'];r=calculate([table[i-1],table[i+1],table[i+2]] if i+2<len(table) else [table[i-2],table[i-1],table[i+1]],q)
 for k in ['total_pressure_Pa','static_pressure_Pa']:
  delta=r[k]-table[i][k];assert abs(delta)<=.1000000001
  held.append(dict(held_out_flow_L_s=q,field=k,error_Pa=delta,endpoint_and_target_0p1Pa_rounding_compatible=True))
band=square_law_rounding_band(table,flow_half_step_L_s=.5,pressure_half_step_Pa=.05);assert all(r['compatible'] for r in band['fields'].values())
rows=[];case_summaries={}
for condition in ['maximum','minimum']:
 F=R/'smooth-rigid-bend-source-reviewed'/condition;case=json.loads((F/'analysis.json').read_text());data=json.loads((F/'fitting-data.json').read_text());led=ledger(case,data);assert led==json.loads((F/'pressure-ledger.json').read_text());case_rows=[]
 for path in led['outlet_paths']:
  g=path['outlet_port_guid'];port=case['port_flows'][g];q=port['flow_m3_s']*1000;r=calculate(table,q);row=dict(condition=condition,terminal=port['source_section'],terminal_connection_port_guid=g,design_flow_L_s=q,catalogue_terminal_Pt_Pa=r['total_pressure_Pa'],catalogue_terminal_Ps_Pa=r['static_pressure_Pa'],linear_flow_terminal_Pt_Pa=r['linear_flow_comparison_total_pressure_Pa'],represented_straight_partial_Pa=path['known_straight_friction_Pa'],conditional_component_partial_Pa=path['conditional_signed_table_subtotal_Pa'],conditional_known_budget_with_terminal_Pa=math.fsum([path['known_straight_friction_Pa'],path['conditional_signed_table_subtotal_Pa'],r['total_pressure_Pa']]),remaining_component_gaps=len(path['numerically_unresolved_fitting_paths']),complete_pressure_Pa='Unknown');assert row['remaining_component_gaps']==3;rows.append(row);case_rows.append(row)
 assert len(case_rows)==80
 case_summaries[condition]=dict(terminals=80,flow_range_L_s=[min(r['design_flow_L_s'] for r in case_rows),max(r['design_flow_L_s'] for r in case_rows)],conditional_catalogue_Pt_range_Pa=[min(r['catalogue_terminal_Pt_Pa'] for r in case_rows),max(r['catalogue_terminal_Pt_Pa'] for r in case_rows)],complete_pressure_verified=False,remaining_unique_component_gaps=104)
# Bounded-input controls independent of source reconciliation.
for q in [32.,298.,True]:
 try:calculate(table,q)
 except ValueError:pass
 else:raise AssertionError('Unbounded/type input accepted')
# Source terminal pressure is kept a separate boundary load, not inserted as a fitting K.
summary=dict(source_performance_pdf_sha256=sha(source),source_locator='PDF2/printedB1-12 nominal8in,24x24in/600x600mm panel,no damper',source_page_actually_viewed=True,source_logical_ifc_sha256=sha(R/'Supply Air Logical Network.ifc'),pressure_method_sha256=sha(A/'src/bsa/terminal_pressure_curve.py'),source_catalogue_reader_sha256=sha(A/'src/bsa/manufacturer_adpi.py'),source_rows=9,source_flow_domain_L_s=[33,297],pressure_method='Piecewise linear pressure in squared flow;explicit study assumption supported by held-out source rows',held_out_pressure_checks=held,rounding_compatibility_band=band,KSelect_toolkit_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=T,text=True).strip(),native_comparisons=native,terminal_pressure_rows=len(rows),cases=case_summaries,input_rejection_controls=3,room_static_reference='Assumed common0Pa gauge for conditional boundary-budget comparison,not measured room pressure',pressure_boundary_scope='Catalogue total-pressure requirement at nominal terminal neck relative to room;actual connection plane/collar/installation correspondence pending',original_pressure_ledgers_unchanged=True,course_and_manufacturer_ADPI_unchanged=True,installed_terminal_pressure_verified=False,physical_joint_verified=False,complete_pressure_verified=False,fan_duty_Pa=None,design_accepted=False)
(O/'review.json').write_text(json.dumps(summary,indent=2))
with (O/'Terminal Pressure and Conditional Path Budget.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(dict(native_comparisons=native,cases=case_summaries,held_out_checks=len(held),rows=len(rows))))
