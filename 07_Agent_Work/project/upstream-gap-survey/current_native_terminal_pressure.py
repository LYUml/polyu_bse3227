from pathlib import Path
import json,csv,hashlib,math
from decimal import Decimal,localcontext
import ifcopenshell
from ifcopenshell.util.system import get_port_element
from fluids.numerics import interp
from bsa.manufacturer_adpi import catalogue
from bsa.terminal_pressure_curve import calculate
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';O=B/'current-native-terminal-pressure'
load=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=B/'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc';assert sha(model)=='a26626e4359ca82ca90de33423d46819b66bd78e54f22a0f52e221ff18ce2937'
m=ifcopenshell.open(model)
source=P/'05_Calculations/Connection_Layout/Current Open Plenum Study/Terminal Boundary Pressure Budget.csv'
before=sha(source);old=list(csv.DictReader(source.open(encoding='utf-8-sig')))
batch=load(B/'current-course-kselect-all-conditions/batch-complete.json')
reports={r['effective_cfm']:load(Path(r['folder'])/'result.json') for r in batch['records']}
indexfile=P/'03_Design_Drawings/Connection_Layout/Current Open Plenum Study/Drawing Component Index.csv'
index={r['native_port_guid']:r for r in csv.DictReader(indexfile.open(encoding='utf-8-sig')) if r['label'].startswith('SD-')}
course=list(csv.DictReader((P/'05_Calculations/Connection_Layout/Native K-Select Ratio Check.csv').open(encoding='utf-8-sig')))
cflows={(r['terminal'],r['case']):r for r in course}
table=catalogue(P/'07_Agent_Work/project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf')['8']
rows=[];checks=0;scope_cases={}
with localcontext() as context:
 context.prec=40
 for row in old:
  port=row['outlet_port_guid'];owner=get_port_element(m.by_guid(port)).GlobalId
  assert index[port]['product_guid']==owner==row['native_endpoint_owner_guid']
  terminal=row['terminal'];assert index[port]['label']==terminal
  flow=float(row['design_flow_L_s']);course_row=cflows[(terminal,row['condition'])]
  assert math.isclose(float(course_row['flow_L_s']),flow,rel_tol=1e-12)
  cfm=int(course_row['effective_cfm']);result=reports[cfm];assert result['ok'] and all(result['checks'].values())
  assert result['report']['sha256']==course_row['native_pdf_sha256']
  pressure=result['report']['selected']['pressure_in_wc']*249.08891
  raw=result['report']['table'];x=raw['airflow_cfm'];y=raw['pressure_in_wc'];target=flow*2.118880003289315
  assert x[0]<=target<=x[-1]
  # Bounded comparison interpolation; this is not the manufacturer's hidden algorithm.
  estimated=interp(target**2,[v*v for v in x],y)*249.08891
  i=next(i for i in range(len(x)-1) if x[i]<=target<=x[i+1])
  D=lambda v:Decimal(str(v))
  fraction=(D(target)**2-D(x[i])**2)/(D(x[i+1])**2-D(x[i])**2)
  exact=(D(y[i])+fraction*(D(y[i+1])-D(y[i])))*D(249.08891)
  assert math.isclose(float(exact),estimated,rel_tol=1e-12);checks+=1
  catalog=calculate(table,flow)['total_pressure_Pa']
  assert math.isclose(catalog,float(row['conditional_terminal_total_pressure_Pa']),rel_tol=1e-12)
  partial=math.fsum([float(row['represented_straight_partial_Pa']),float(row['conditional_component_partial_Pa'])])
  budget=math.fsum([partial,estimated])
  assert int(row['remaining_component_gaps'])==2
  rows.append({'condition':row['condition'],'terminal':terminal,'native_endpoint_guid':owner,'outlet_port_guid':port,'design_flow_L_s':flow,'effective_native_CFM':cfm,'effective_native_flow_L_s':result['report']['si']['airflow_lps'],'reported_native_terminal_Pt_Pa':pressure,'comparison_native_table_Pt_at_design_flow_Pa':estimated,'prior_catalogue_terminal_Pt_Pa':catalog,'comparison_terminal_Pt_difference_Pa':estimated-catalog,'represented_partial_excluding_terminal_Pa':partial,'comparison_partial_with_native_terminal_Pt_Pa':budget,'prior_conditional_partial_with_terminal_Pa':row['conditional_budget_with_terminal_Pa'],'remaining_numeric_component_gaps':2,'complete_pressure_Pa':'Unknown','actual_controlled_VAV_loss_Pa':'Unknown','native_pdf_sha256':result['report']['sha256']})
 assert len(rows)==160 and len({(r['terminal'],r['condition']) for r in rows})==160
for condition in ['maximum','minimum']:
 rs=[r for r in rows if r['condition']==condition]
 scope_cases[condition]={'terminals':len(rs),'reported_native_terminal_Pt_range_Pa':[min(r['reported_native_terminal_Pt_Pa'] for r in rs),max(r['reported_native_terminal_Pt_Pa'] for r in rs)],'comparison_native_table_Pt_at_design_flow_range_Pa':[min(r['comparison_native_table_Pt_at_design_flow_Pa'] for r in rs),max(r['comparison_native_table_Pt_at_design_flow_Pa'] for r in rs)],'comparison_minus_catalogue_Pt_range_Pa':[min(r['comparison_terminal_Pt_difference_Pa'] for r in rs),max(r['comparison_terminal_Pt_difference_Pa'] for r in rs)],'remaining_unique_numeric_component_gaps':84}
with (O/'Native Terminal Pressure Comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert sha(source)==before and sha(model)=='a26626e4359ca82ca90de33423d46819b66bd78e54f22a0f52e221ff18ce2937'
r={'scope':'Separate current-source native terminal total-pressure comparison; not replacement/adoption of original pressure budget','pressure_quantity_source':load(O/'pressure-type-source.json'),'guide_source':{'sha256':sha(P/'07_Agent_Work/project/adpi-manufacturer-study/GRD_Engineering.pdf'),'page':8,'printed_page':'a1-8','actual_page_rendered_and_viewed':True,'finding':'Manufacturer describes inlet total/static pressure measurement at least1.5duct diameters upstream, with traverse/static-regain qualifications; actual IFC station correspondence not verified'},'native_catalogue_equal_effective_flow_check':load(O/'effective-flow-catalogue-comparison.json'),'native_conditions':49,'terminal_rows':160,'native_IFC_endpoint_and_drawing_index_matches':160,'course_flow_and_report_hash_matches':160,'independent_Decimal_interpolation_checks':checks,'source_ifc_sha256':sha(model),'source_budget_sha256':before,'source_budget_and_IFC_unchanged':True,'drawing_index_sha256':sha(indexfile),'comparison_csv_sha256':sha(O/'Native Terminal Pressure Comparison.csv'),'cases':scope_cases,'interpolation_basis':'Bounded piecewise linear pressure versus squared CFM using actual nine-column native report tables; comparison assumption, not verified manufacturer algorithm','pressure_added_once':True,'static_and_velocity_pressure_added_again':False,'limits':['Native pressure has0.01in.wc display resolution; assumed half-step compatibility is not accuracy','Interpolated displayed table values are conditional comparisons, not higher-precision native results','Room static common0Pa and installation/test-plane correspondence remain assumptions','Fully-open VAV comparison does not establish controlled VAV operating loss','Each path retains2numeric component gaps;84unique gaps overall','No complete pressure, critical path, fan duty or ADPI acceptance'],'complete_pressure_Pa':None,'hydraulic_critical_path':None,'fan_duty_Pa':None,'ADPI_verified':False,'design_accepted':False}
(O/'review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':checks,'cases':scope_cases}))
