from pathlib import Path
import csv,json,hashlib,math,shutil
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader,PdfWriter
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=B/'07_Agent_Work/runs/course-report-bse3125-style';R.mkdir(exist_ok=False)
paths={'online':B/'05_Calculations/Connection_Layout/Online Ductulator Check.csv','ratios':B/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv','ducts':B/'05_Calculations/Connection Layout Duct Sizing.csv','vav':B/'05_Calculations/Connection_Layout/VAV Connection Schedule.csv','plan':B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.pdf','allocation':B/'07_Agent_Work/runs/vav-recenter-design-reviewed/delivery/allocation/allocation.json'}
paths['flex_budget']=B/'07_Agent_Work/runs/current-flex-length-budget/review.json'
paths['hk_flex_design']=B/'05_Calculations/Connection_Layout/Flexible Connection Design Budget.json'
paths['course_basis']=B/'07_Agent_Work/project/coursework-proportionate-design-decision.json'
paths['native_check']=B/'05_Calculations/Connection_Layout/Final Native Drawing Check.json'
paths['original_dwg']=B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.dwg'
paths['kselect_check']=B/'07_Agent_Work/runs/current-course-kselect-review/review.json'
paths['kselect_ratios']=B/'07_Agent_Work/runs/current-course-kselect-review/Native K-Select Ratio Check.csv'
kselect=json.loads(paths['kselect_check'].read_text());assert kselect['native_conditions']==49 and kselect['directional_operating_checks']==640 and kselect['all640_reported_native_ratios_within_classroom_interval']
previous=B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf'
shutil.copy2(previous,R/'Previous Coursework Report.pdf')
native_check=json.loads(paths['native_check'].read_text());assert hashlib.sha256(paths['original_dwg'].read_bytes()).hexdigest()==native_check['original_dwg_sha256'];assert native_check['native_geometry']['generated_native_correspondence'] and native_check['fresh_flex_check']['routes']==80 and native_check['visual_review']['actual_A1_plot_inspected']
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
def read(k):return list(csv.DictReader(paths[k].open()))
a=read('ratios');duct=read('ducts');vav=read('vav');online={r['Section']:r for r in read('online')};allocation=json.loads(paths['allocation'].read_text());terms={t['id']:t for t in allocation['terminals']};assert len(a)==640 and len(duct)==47 and len(vav)==20 and len(terms)==80
by=defaultdict(list)
for row in a:by[row['terminal']].append(row)
assert set(by)==set(terms)
for v in vav:
 ids=v['Diffuser outlets'].split(', ');assert len(ids)==int(v['Outlets'])==4;assert abs(sum(terms[i]['maximum_flow_L_s'] for i in ids)-float(v['Qmax L/s']))<=.050001
q=sum(t['maximum_flow_L_s'] for t in terms.values());assert abs(q-12000.372763419484)<1e-8
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.graphics.shapes import Drawing,String
from reportlab.graphics.charts.lineplots import LinePlot
import html
for alias,name in [('Body','times.ttf'),('Bold','timesbd.ttf'),('Italic','timesi.ttf')]:pdfmetrics.registerFont(TTFont(alias,'C:/Windows/Fonts/'+name))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
W=A4[0]-144;story=[]
body=ParagraphStyle('Body',fontName='Body',fontSize=12,leading=15,alignment=TA_JUSTIFY,spaceAfter=8)
heading=ParagraphStyle('H1',parent=body,fontName='Bold',fontSize=15,leading=19,spaceAfter=12,keepWithNext=True,alignment=0)
subheading=ParagraphStyle('H2',parent=body,fontName='Bold',fontSize=12,leading=15,spaceBefore=7,spaceAfter=6,keepWithNext=True,alignment=0)
small=ParagraphStyle('Small',parent=body,fontSize=9.5,leading=11,spaceAfter=4,alignment=0)
caption=ParagraphStyle('Caption',parent=small,fontName='Italic',alignment=TA_CENTER,spaceAfter=9)
def p(text,style=body):story.append(Paragraph(text,style))
def sub(text):p(text,subheading)
def page(title):
 if story:story.append(PageBreak())
 p(title,heading)
def table(title,head,rows,widths):
 p(title,ParagraphStyle('TableTitle',parent=small,fontName='Bold',keepWithNext=True,spaceAfter=5))
 total=sum(widths);values=[[Paragraph(html.escape(str(c)).replace('\n','<br/>'),ParagraphStyle('Cell',parent=small,fontName='Bold' if i==0 else 'Body',spaceAfter=0)) for c in row] for i,row in enumerate([head]+rows)]
 t=Table(values,colWidths=[v/total*W for v in widths],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEABOVE',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.7,colors.black),('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5)]));story.extend([t,Spacer(1,8)])
def footer(c,doc):c.setFont('Body',9);c.drawCentredString(A4[0]/2,34,str(doc.page))
p('Open-plan Office Air-conditioning Design',ParagraphStyle('Title',parent=heading,fontSize=22,leading=26,alignment=TA_CENTER,spaceAfter=5));p('BSE3227: HVACR 1',ParagraphStyle('Subtitle',parent=body,alignment=TA_CENTER,spaceAfter=15))
p('1. Introduction and design basis',heading);sub('1.1 Design objective')
p('The design provides a variable air volume supply-air layout for the given open-plan office. It covers the preliminary cooling load, maximum and minimum diffuser flows, classroom air-diffusion checks, VAV connections and rectangular duct sizing required by the assignment [1].')
sub('1.2 Adopted office and system assumptions')
p('The supplied plan annotation of 1022 m<super>2</super> is used for the rule-of-thumb load calculation. The interpreted CAD boundary is used for diffuser locations and directional lengths. These are different quantities: the annotated area is not presented as a surveyed net area. The adopted layout has 80 diffusers, twenty VAV groups and 47 rigid supply sections.')
table('Table 1. Principal design inputs.',['Parameter','Adopted value'],[['Office load area','1022 m2, supplied plan'],['Cooling allowance / sensible factor','189 W/m2 / 0.90, classroom guide'],['Room / supply temperature','24 / 12 deg C, design assumption'],['Density / specific heat','1.20 kg/m3 / 1006 J/(kg K)'],['Minimum airflow','40% of maximum'],['Diffuser family / neck','1400/51400 four-cone, 600 x 600 mm / 8 inch'],['Ordinary flexible-connection design cap','4.00 m; additional routing allowance 0.50 m']],[1,1.3])
sub('1.3 Calculation scope')
p('The empirical allowance and routing allowance are preliminary design assumptions. This report distinguishes the classroom ratio check from a measured ADPI percentage. Full fan selection and detailed system pressure are supplementary engineering studies, not part of the assignment duct-sizing calculation.')
page('2. Cooling load, airflow and VAV layout');sub('2.1 Preliminary thermal balance')
p('The written classroom guide gives an office cooling allowance of 189 W/m<super>2</super> and an approximate sensible heat factor of 0.90 [2]. The same basis is used throughout:')
table('Table 2. Thermal balance and supply airflow.',['Calculation','Result'],[['Total cooling = 1022 x 189','193.158 kW thermal'],['Sensible cooling = 193.158 x 0.90','173.8422 kW thermal'],['Q = sensible W / [density x cp x (24 - 12)]','12000.373 L/s'],['Minimum supply = 0.40 x maximum','4800.149 L/s']],[1.7,1])
p('These thermal powers are not electrical input ratings. The temperature difference and air properties in Table 1 are adopted for this preliminary air balance. Unrounded flows are used for calculations; displayed schedule values are rounded.')
sub('2.2 Diffuser distribution and VAV grouping')
p('Each diffuser receives its assigned share of the total airflow. The 80 maximum flows sum to 12000.373 L/s, and every minimum flow is exactly 40% of its maximum. Each of the twenty VAV groups serves four diffusers, satisfying the assignment requirement for four to five outlets per box. Group flows equal the sum of their diffuser flows; the complete grouping is given in Appendix C.')
sub('2.3 Flexible connection design')
p('The longest straight XY connection reconstructed from the saved/reopened drawing is 2.873 m. Adding the stated 0.50 m routing allowance gives 3.373 m. This leaves a minimum conditional margin of 0.627 m to the adopted 4 m design cap, which is stricter than the assignment limit of 5 m. The allowance is not a measured vertical offset or installed slack.')
p('Flexible ducts are specified as final connections, not main distribution. Final routing must remain within the ordinary limit and must not pass through fire-resisting barriers or attach directly to fire/fire-smoke dampers [6]. The actual installed lengths and fire-boundary classification would be confirmed before installation.')
page('3. Diffuser selection and air-diffusion checks');sub('3.1 Selected diffuser and characteristic length')
p('The selected Krueger 1400/51400 has a 600 x 600 mm panel, 8-inch neck and no damper [3]. Both operating flows of all 80 diffusers lie within its published table. T<sub>0.25</sub> is taken from the third horizontal isothermal throw value; intermediate flows use linear interpolation between adjacent published rows.')
p('Characteristic length L is taken in each principal plan direction to a boundary or the midplane between opposing outlets, following the classroom method [2]. The 320 directional lengths comprise 40 boundary-limited and 280 opposing-outlet cases. Appendix B records all four lengths for every diffuser.')
sub('3.2 Maximum and minimum operating cases')
p('All 640 directional operating cases lie within the adopted classroom interval T<sub>0.25</sub>/L = 1.0-3.4. Original catalogue interpolation gives 1.1098-3.2245; the independent native K-Select check gives 1.2066-3.2797 [4]. Figure 1 shows the directional extremes for each diffuser using the original table.')
d=Drawing(W,165);chart=LinePlot();chart.x=35;chart.y=30;chart.width=W-48;chart.height=120
ordered=sorted(by,key=lambda v:int(v.split('-')[1]));high=[max(float(v['ratio']) for v in by[k] if v['case']=='maximum') for k in ordered];low=[min(float(v['ratio']) for v in by[k] if v['case']=='minimum') for k in ordered]
chart.data=[list(zip(range(1,81),high)),list(zip(range(1,81),low)),[(1,1),(80,1)],[(1,3.4),(80,3.4)]];chart.xValueAxis.valueMin=1;chart.xValueAxis.valueMax=80;chart.xValueAxis.valueSteps=[1,20,40,60,80];chart.yValueAxis.valueMin=.8;chart.yValueAxis.valueMax=3.6;chart.yValueAxis.valueSteps=[1,2,3,3.4]
for axis in [chart.xValueAxis,chart.yValueAxis]:axis.labels.fontName='Body';axis.labels.fontSize=8
for i,color in enumerate([colors.black,colors.HexColor('#666666'),colors.HexColor('#999999'),colors.HexColor('#999999')]):chart.lines[i].strokeColor=color;chart.lines[i].strokeWidth=.8
chart.lines[1].strokeDashArray=[3,2];chart.lines[2].strokeDashArray=[1,2];chart.lines[3].strokeDashArray=[1,2];d.add(chart);d.add(String(W/2,6,'Diffuser number; solid = maximum-case upper extreme, dashed = minimum-case lower extreme',fontName='Body',fontSize=8,textAnchor='middle'));story.append(d);p('Figure 1. Original-table directional ratio extremes and adopted classroom bounds.',caption)
sub('3.3 Interpretation and design approximation')
p('The preliminary sensible allowance is 170.1 W/m<super>2</super>, 6.3% above the printed classroom table limit of 160 W/m<super>2</super>. Using the classroom interval at this allowance is an explicit coursework design approximation. It is not a teacher-issued exemption, a prediction of ADPI &gt;=80%, or a transfer of the manufacturer Type 3 curve. No measured ADPI percentage is claimed.')
page('4. Duct sizing and Hong Kong design provisions');sub('4.1 Rigid duct arrangement and sizing')
p('The single-line plan connects the VAV groups to a branched supply trunk using straight sections where practical. Each of the 47 sections is identified on the drawing and in Appendix D. Rectangular area determines actual air velocity; the adopted main/branch speed limits are 10/8 m/s. The upper friction criterion is 1.23 Pa/m and the preferred aspect-ratio limit is 4:1 [2].')
p('All 47 adopted sections were checked in the assignment-linked Online Ductulator using 36 unique input combinations [5]. D06, D13 and D20 use 550 x 350 mm. The schedule retains both the online friction value and an independent equivalent-round calculation; the two are not assumed numerically identical. Section friction is a pressure gradient, not total fitting, terminal or fan pressure.')
sub('4.2 Applicable provisions and design checks')
table('Table 3. Course criteria and scoped Hong Kong design checks.',['Item / basis','Adopted design response','Scope'],[['Course: VAV outlets [1]','Twenty groups, four outlets each','Numerically checked'],['Course: minimum flow [1]','40% for all 80 diffusers','Numerically checked'],['Course: section sizing [2,5]','47 sections within adopted speed/friction/aspect limits','Section sizing only'],['FSD 7.2: ordinary flexible length [6]','4 m design cap; maximum conditional budget 3.373 m','Routing allowance assumed'],['FSD 7.3-7.4: flexible routing [6]','Final connections only; no fire-barrier crossing or direct fire-damper attachment specified','Installation must confirm'],['EMSD BEC 2024 [7]','Energy provisions apply where within statutory scope','Full-system energy compliance not established']],[1.3,1.7,1])
p('The FSD provisions are incorporated as design constraints. The BEC governs wider air-conditioning energy matters; this floor distribution exercise does not establish whole-system fan power, plant efficiency or complete statutory compliance. Applicable installation, insulation, controls and fire-stopping details require confirmation in a real project.')
page('5. Design assessment and conclusion');sub('5.1 Consistency of the adopted design')
p('The report, diffuser schedule, VAV grouping and duct schedule refer to one 80-diffuser design. The CAD was saved and reopened in AutoCAD; generated geometry and all 80 straight connection lengths were checked against the calculation sources. The reviewed A1 plot uses a 1:100 scale, with a 100 mm reference measured at 99.991 mm. The formal drawing is included after the appendices.')
sub('5.2 Independent calculation checks')
p('Native K-Select GRD reports cover all 160 terminal operating flows through 49 distinct whole-CFM inputs. Inputs differ from the prescribed flow by no more than 0.2331 L/s. Independent PDF-coordinate checks reconcile the reported conditions and results. The source imperial throw units are converted to metres; a low-flow NC dash remains qualified unknown. These checks support numerical consistency, not installed performance certification.')
sub('5.3 Conclusion and limitations')
p('The adopted design provides 12000.373 L/s maximum and 4800.149 L/s minimum supply air through twenty four-outlet VAV groups. All classroom directional ratio checks meet the selected interval under the stated load-range approximation. The 47 rigid duct sections meet the adopted sizing criteria, and the conditional flexible-connection budget is below the stricter 4 m design cap.')
p('The result is a preliminary coursework design. Its principal limitations are the empirical cooling allowance, table-range approximation, interpreted plan boundaries and routing allowance. Actual ceiling conditions, final installed lengths and product installation would require confirmation before construction. Full-system pressure and fan selection remain separate engineering work; supplementary linear-slot and CFD studies do not replace the specified 1400/51400 coursework design.')
page('References')
refs=['[1] The Hong Kong Polytechnic University, BSE3227 HVACR 1, Mini-design assignment, 2026/27 Semester 1, pp. 1-2.','[2] BSE3227 classroom guide, Space air diffusion design and air duct sizing, pp. 1, 4-5 and 7-9; classroom recording, 21 October 2026.','[3] Krueger, 1400/51400 Performance Data, 2012, B1-12: 600 x 600 mm panel, no damper, metric horizontal throw.','[4] Krueger GRD Selection 10.0.2, 49 native performance reports for the adopted design, 17 November 2026. Supporting ratio-check records retain effective inputs and original report identities.','[5] Online Ductulator, Metric, V1.0.8, https://ductulator.com/metric/. Assignment-linked tool; 47 sections checked using 36 distinct input sets.','[6] Hong Kong Fire Services Department, Circular Letter No. 2/2023, Fire Safety Requirements for Mechanical Ventilating Systems, paragraphs 7.2-7.4. https://www.hkfsd.gov.hk/eng/source/licensing/MECHANICAL_VS_EN_2_2023.pdf','[7] Electrical and Mechanical Services Department, Code of Practice for Energy Efficiency of Building Services Installation, 2024 Edition. https://www.emsd.gov.hk/beeo/en/mibec_beeo_codtechguidelines.html']
for ref in refs:p(html.escape(ref),ParagraphStyle('Ref',parent=body,fontSize=11,leading=14,spaceAfter=10,alignment=0))
for start in range(0,80,40):
 page('Appendix A. Diffuser operating schedule'+(' (continued)' if start else ''));data=[]
 for ident in ordered[start:start+40]:
  rs=by[ident];maximum=[v for v in rs if v['case']=='maximum'];minimum=[v for v in rs if v['case']=='minimum'];data.append([ident,f"{terms[ident]['maximum_flow_L_s']:.2f}",f"{terms[ident]['minimum_flow_L_s']:.2f}",f"{float(maximum[0]['T025_m']):.3f}",f"{float(minimum[0]['T025_m']):.3f}",f"{max(float(v['ratio']) for v in maximum):.4f}",f"{min(float(v['ratio']) for v in minimum):.4f}"])
 table('Table A1. Original-catalogue flows, throws and directional ratio extremes.',['Outlet','Qmax\nL/s','Qmin\nL/s','Tmax\nm','Tmin\nm','Upper\nT/L','Lower\nT/L'],data,[48,65,65,55,55,76,76])
for start in range(0,80,40):
 page('Appendix B. Characteristic lengths'+(' (continued)' if start else ''));data=[]
 for ident in ordered[start:start+40]:
  rs={r['direction']:r for r in by[ident] if r['case']=='maximum'};data.append([ident]+[f"{float(rs[k]['L_m']):.4f}" for k in ['west','east','south','north']])
 table('Table B1. Plan-direction lengths in metres.',['Outlet','West','East','South','North'],data,[65,95,95,95,95])
page('Appendix C. VAV grouping and connections');p('Group flows are rounded display values. Connection lengths are straight XY geometry, not installed flexible lengths.',small)
table('Table C1. Four-outlet VAV groups.',['VAV','Diffuser outlets','Qmax\nL/s','Qmin\nL/s','XY range\nm'],[[v['VAV'],v['Diffuser outlets'],v['Qmax L/s'],v['Qmin L/s'],v['Min plan m']+'-'+v['Max plan m']] for v in vav],[52,200,59,59,82])
for start in range(0,len(duct),24):
 page('Appendix D. Supply duct sizing'+(' (continued)' if start else ''))
 table('Table D1. Adopted rectangular sections and independent friction checks.',['Section','Flow\nL/s','Size\nmm x mm','Speed\nm/s','Online\nPa/m','Calc\nPa/m','Aspect'],[[r['Section'],f"{float(r['Flow L/s']):.2f}",f"{float(r['Width mm']):.0f} x {float(r['Height mm']):.0f}",f"{float(r['Velocity m/s']):.3f}",online[r['Section']]['Online friction display Pa/m'],f"{float(r['Friction Pa/m']):.4f}",f"{float(r['Aspect ratio']):.2f}"] for r in duct[start:start+24]],[44,63,90,57,57,57,45])
bodyfile=R/'Report Body.pdf';SimpleDocTemplate(str(bodyfile),pagesize=A4,leftMargin=72,rightMargin=72,topMargin=62,bottomMargin=62).build(story,onFirstPage=footer,onLaterPages=footer)
w=PdfWriter();w.append(bodyfile);w.append(paths['plan']);out=R/'BSE3227 HVAC Mini-Design.pdf'
with out.open('wb') as f:w.write(f)
assert hashes=={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
review=dict(scope='Coursework report styled after userBSE3125, source-consistent80terminal baseline; not construction/statutory or measuredADPI acceptance',inputs=hashes,body_pages=len(PdfReader(bodyfile).pages),total_pages=len(PdfReader(out).pages),output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source_files_unchanged=True,design_accepted=False,reference_report_sha256='62036e4b3957cbde931a18bb23ed0d3a43d3e7c6604944774d3132315fa66a50',format=dict(font='Times New Roman',body_pt=12,leading_pt=15,numbered_sections=True))
(R/'build-review.json').write_text(json.dumps(review,indent=2));print(json.dumps(dict(total_pages=review['total_pages'],output_sha256=review['output_sha256'])))
