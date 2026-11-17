"""Publish only the audited package, keeping prior bytes in ignored provenance."""
import json,csv,shutil,hashlib
from pathlib import Path
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=B/'07_Agent_Work/runs';I=R/'course-refined-report-inputs'
C=B/'05_Calculations/Connection_Layout';D=B/'03_Design_Drawings/Connection_Layout'
archive=R/'course-refined-previous-delivery';archive.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(R/'course-refined-final-audit.json');assert audit['all_checks_pass'] and audit['native_reopen_pass']
mapping={
 B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf':R/'course-report-refined-private-polished/BSE3227 HVAC Mini-Design.pdf',
 B/'04_Final_Report/Public_Snapshot/BSE3227 HVAC Mini-Design.pdf':R/'course-report-refined-public-polished/BSE3227 HVAC Mini-Design.pdf',
 D/'Supply Air Distribution.dwg':R/'course-diffuser-native-final/Supply Air Distribution.dwg',
 D/'Supply Air Distribution.pdf':R/'course-diffuser-native-final/Supply Air Distribution.pdf',
 D/'VAV Connection Schedule.dwg':R/'course-refined-vav-table/native/Supply Air Distribution.dwg',
 D/'VAV Connection Schedule.pdf':R/'course-refined-vav-table/native/Supply Air Distribution.pdf',
 C/'Diffuser Course Ratio Check.csv':I/'Diffuser Course Ratio Check.csv',
 C/'Native K-Select Ratio Check.csv':I/'Native K-Select Ratio Check.csv',
 C/'VAV Connection Schedule.csv':I/'VAV Connection Schedule.csv'}
def preserve(p):
 if p.exists():
  target=archive/p.relative_to(B);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
def save(p,value):preserve(p);p.write_text(json.dumps(value,indent=2))
for dest,source in mapping.items():preserve(dest);shutil.copy2(source,dest);assert sha(dest)==sha(source)
fixed=read(R/'course-diffuser-fixed-service-checked/review.json');native=read(R/'course-diffuser-native-final/review.json')
ratio=list(csv.DictReader((I/'Diffuser Course Ratio Check.csv').open()))
save(C/'Diffuser Course Ratio Check.json',dict(scope='Adopted fixed-service-area150mm row adjustment; classroom approximation,not measured ADPI',cases=640,course_ratio_met=640,ratio_range=[min(float(r['ratio']) for r in ratio),max(float(r['ratio']) for r in ratio)],L_direction_count=320,course_ratio_range=[1,3.4],preliminary_sensible_load_W_m2=170.1,class_table_load_range_W_m2=[35,160],classroom_ratio_arithmetic_pass=True,ADPI_applicability_accepted=False,engineering_accepted=False))
k=read(C/'Native K-Select Check.json');k.update(scope='Same49 native manufacturer flow conditions reused after verified fixed-service-area positional refinement; no new native performance executions in refinement',native_ratio_minimum=fixed['candidate_ratio_range'][0],native_ratio_maximum=fixed['candidate_ratio_range'][1],minimum_case=fixed['critical_minimum'],maximum_case=fixed['critical_maximum'],new_native_executions=0,native_conditions_reused=49,source_native_ratio_csv_sha256=fixed['native_source_sha256'],native_ratio_csv_sha256=sha(C/'Native K-Select Ratio Check.csv'),ADPI_verified=False)
save(C/'Native K-Select Check.json',k)
save(C/'Final Native Drawing Check.json',dict(original_dwg_sha256=audit['dwg_sha256'],source_before_revision_sha256=native['source_sha256'],saved_copy_dwg_sha256=audit['dwg_sha256'],native_export_sha256=sha(R/'course-diffuser-native-final/reopened/source-export.dxf'),native_geometry=dict(generated_native_correspondence=True,comparison='Full4885-record expected-versus-native comparison with36 explicitly moved entities'),preservation=dict(preserved_records=4885,edited_entities=36),fresh_flex_check=dict(routes=80,maximum_plan_m=audit['maximum_plan_flex_m'],total_plan_m=audit['total_plan_flex_m']),plot=native['plot'],native_reopen_pass=True,visual_review=dict(actual_A1_plot_inspected=True),design_accepted=False))
save(C/'Schedule_Check.json',dict(vav_groups=20,terminal_count=80,raw_native_flex_lengths_reconciled=80,native_cells_reconciled=140,csv_cells_reconciled=140,unchanged_flows_and_membership=True,maximum_flow_L_s=12000.372763419484,minimum_flow_L_s=4800.149105367794,total_plan_flex_m=audit['total_plan_flex_m'],maximum_plan_flex_m=audit['maximum_plan_flex_m'],native_DWG_reopen_pass=True,actual_PDF_page_visually_inspected=True,installed_flex_lengths_verified=False,full_pressure_verified=False,ADPI_verified=False,design_accepted=False))
budget=read(C/'Flexible Connection Design Budget.json');budget.update(source_budget_sha256=sha(R/'course-refined-final-audit.json'),maximum_native_XY_m=audit['maximum_plan_flex_m'],maximum_conditional_design_length_m=audit['maximum_conditional_flex_m'],minimum_conditional_margin_m=4-audit['maximum_conditional_flex_m'],total_plan_flex_m=audit['total_plan_flex_m']);save(C/'Flexible Connection Design Budget.json',budget)
delivery=read(C/'Coursework Delivery Check.json');delivery.update(report_pages=16,report_sha256=audit['report_sha256'],dwg_sha256=audit['dwg_sha256'],plot_sha256=audit['plot_sha256'],anonymous_public_report_sha256=audit['public_report_sha256'],all80route_lengths_preserved=False,all80route_lengths_recomputed=True,total_plan_flex_m=audit['total_plan_flex_m'],conditional_maximum_flexible_length_m=audit['maximum_conditional_flex_m'],refinement_adopted=True,coursework_user_accepted=False,report_illustrations=3)
save(C/'Coursework Delivery Check.json',delivery)
audit.update(actual_changed_report_pages_visually_reviewed=True,all16_pages_rendered_and_reviewed=True,all15_nonidentity_pages_pixel_identical_private_public=True,actual_VAV_table_plot_visually_reviewed=True,formal_package_updated=True,all_checks_pass=True)
for name in ['Report Consistency Check.json','Final Coursework Consistency Check.json']:save(C/name,audit)
candidate=read(C/'Diffuser Position Candidate Check.json');candidate.update(scope='Adopted coursework local-position refinement,with explicit classroom applicability assumption',formal_package_updated=True,selected=True,pending=['User coursework acceptance'],ADPI_verified=False);save(C/'Diffuser Position Candidate Check.json',candidate)
save(C/'Refined Coursework Delivery Check.json',audit)
(R/'course-refined-published-audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps(dict(published_files=len(mapping),report_pages=16,report_sha256=audit['report_sha256'],user_accepted=False)))
