from pathlib import Path
import json,hashlib
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');R=B/'07_Agent_Work/runs/course-report-supplementary-load'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=read(R/'review.json');review.update(anonymous_first16_pages_pixel_identical=True,appendix_IEEE_references_verified=True,main_coursework_selection='189W/m2 total,0.9sensible,80outlets,20VAV,47sections,600mm/8inch1400family',supplementary_native_conditions=48,supplementary_independent_scalar_checks=2352,supplementary_native_ratio_range=[1.0770514854263322,2.6972680154821953],supplementary_native_reopen_and_plot_visual_review=True,goal_stage='Ready for user review under explicit retained-coursework/appendix-only direction; no automatic expansion',agent_full_goal_complete=False)
for directory in [B/'05_Calculations/Supplementary_Load_Study',A/'docs/evidence']:
 name='Delivery Check.json' if directory.name=='Supplementary_Load_Study' else 'coursework-supplementary-load-delivery.json'
 (directory/name).write_text(json.dumps(review,indent=2))
anon=B/'04_Final_Report/Public_Snapshot/BSE3227 HVAC Mini-Design.pdf'
for name in ['Final Coursework Consistency Check.json','Refined Coursework Delivery Check.json']:
 path=B/'05_Calculations/Connection_Layout'/name;d=read(path)
 d.update(pages=18,report_pages=18,report_sha256=review['report_sha256'],public_report_sha256=sha(anon),anonymous_public_report_sha256=sha(anon),previous16page_audit_preserved=True,all16_main_pages_pixel_identical_to_prior=True,added_appendix_pages=2,appendix_visual_review=True,reference_count=8,main_engineering_unchanged=True,supplementary_design_adopted=False,coursework_user_accepted=False,supplementary_delivery_check='05_Calculations/Supplementary_Load_Study/Delivery Check.json')
 path.write_text(json.dumps(d,indent=2))
course='''# BSE3227 HVAC mini-design

Current review package: **18-page report**, retaining the coursework main design
(189 W/m2 total, sensible factor0.90,80diffusers,20VAV groups,47rigid sections,
600mm/8inch1400/51400). The native DWG, plot and main engineering schedules are
unchanged. The first16report pages are pixel-identical to the previous package.
User direction is to retain the course solution and keep own-method alternatives
in an appendix; no product/load substitution is adopted.

[Formal PDF with authorized group members](04_Final_Report/Connection_Layout/BSE3227%20HVAC%20Mini-Design.pdf)
and [anonymous PDF](04_Final_Report/Public_Snapshot/BSE3227%20HVAC%20Mini-Design.pdf)
now include a two-page Appendix E. It compares an explicitly assumed150W/m2
load with a6inch neck, retaining the prescribed product family and layout.
48actual K-Select conditions,2352independent scalar checks,640directional checks
and47actual Online Ductulator checks support that supplementary comparison.
[Supplementary evidence](05_Calculations/Supplementary_Load_Study/Delivery%20Check.json)
keeps it separate from the main submission.

The main design still has170.1W/m2 sensible duty above the classroom160W/m2
table limit. Its1.2117-3.1122 ratio range uses an explicit coursework approximation;
no measured ADPI or manufacturer Type3 pass is claimed. Conditional flexible
length3.373m is below the4m ordinary design cap, assuming0.50m additional routing.
Actual installation and full statutory compliance are unestablished.
Ready for user review; acceptance remains unconfirmed. Automatic research stops
at this handoff. Earlier entries below describe historical studies.

'''
p=B/'README.md';old=p.read_text(encoding='utf-8');old=old[old.index('Axial bend refinement'):];p.write_text(course+old,encoding='utf-8')
status='''## Current coursework handoff - retained course basis

The user explicitly retained the coursework main solution; alternative methods
belong in an appendix. The18-page report retains all16main pages unchanged and
adds two reviewed pages: external HKIE load benchmark, declared margin, actual
48-condition K-Select/2352scalar/640ratio checks, recalculated47section sizes and
actual36-query Online Ductulator results. The alternative150W/m2/6inch selection
is unadopted; main189W/m2/8inch drawings and schedules are unchanged.
189 is an optional preliminary classroom reference, not a fixed value in the
original assignment brief. Keep source authority distinct from design assumptions.
Main170.1>160W/m2 applicability remains explicit; neither source-curve prediction
nor successful ratio arithmetic establishes physical ADPI/manufacturer Type3 pass.
The finite coursework package is ready for user review, not user-accepted.
Full agent/pressure/CFD goals remain in the roadmap; stop automatic expansion.
See [new delivery evidence](evidence/coursework-supplementary-load-delivery.json).

'''
for name in ['README.md','docs/ROADMAP.md','docs/AGENT_STATUS.md']:
 p=A/name;p.write_text(status+p.read_text(encoding='utf-8'),encoding='utf-8')
p=A/'docs/CURRENT_COURSE_CLOSEOUT.md';old=p.read_text(encoding='utf-8');old=old[old.index('The user-authorized refinement'):];p.write_text('# Current BSE3227 coursework review package\n\n'+status+'## Previous16-page refinement (retained main pages)\n\n'+old,encoding='utf-8')
p=A/'docs/REUSE_SURVEY.md';p.write_text('''## Retained-coursework appendix milestone

No new solver or CAD engine added. The actual alternative reuses the pinned
K-Select toolkit0.1.1/Apache-2.0 commit3eecd3710e976927c4b7c639900e833d12150453,
ezdxf1.4.5(MIT), Shapely2.2.0(BSD-3-Clause), fluids1.3.1(MIT), existing guarded
native revision/VAV/duct adapters and ReportLab4.4.9(BSD-3-Clause). PyMuPDF1.26.7
(AGPL-3.0 runtime) independently reads/render-checks reports; no runtime bundled.
OnlineDuctulator V1.0.8 is checked as a website, not imported/copied code.
48native exports,2352independent scalars,375native schedule fields and1280ratio
recomputations execute. Main engineering is preserved under user instruction.
See [executed evidence](evidence/coursework-supplementary-load-delivery.json).

'''+p.read_text(encoding='utf-8'),encoding='utf-8')
p=A/'runs/CONTINUE_AGENT.md';p.write_text(p.read_text(encoding='utf-8')+'\nUSER latestdirection RETAINCOURSE main189/.9/8inch1400; alternatives onlyAPPENDIX. New18page formal+anon reports published;first16pixelidentical,2appendixpagesACTUALLYVIEWED. MainDWG/plot/duct/VAV/640datahashespreserved. Supplement150/6inch historicalHKIE129+15percent rounded assumption,notadopted;48nativeKselect/2352independentchecks/640ratios1.07705..2.69727;47corridor-nonincreasing sizes actualbrowser36queries;375nativefields+1280Decimalratios checked;main+VAVsupplementplotsACTUALLYVIEWED/reopened. Public05SupplementaryLoadStudy separate;course/rootpublicdeliveryJSON. Sourceauthority189OPTIONALnotbriefmandatory corrected. Main170.1>160courseapprox remains/notphysicalADPI/notType3pass. Stage/pushbothnext,thenready-userreviewhandoff;doNOTexpandCFD/pressure/research orclaimuseraccepted.\n',encoding='utf-8')
print('Recorded separate main/supplementary delivery and reuse evidence')
