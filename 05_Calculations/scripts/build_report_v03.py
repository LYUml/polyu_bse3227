"""Course-basis report with complete schedules, generated from v03 data."""
from pathlib import Path
import csv,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data'
def read(n):return list(csv.DictReader((D/n).open()))
b=json.loads((D/'design_basis_v03.json').read_text());diff=read('diffusers_v03.csv');duct=read('ducts_v03.csv');vav=read('vav_boxes_v03.csv');flex=read('flex_routes_v03.csv')
s=getSampleStyleSheet();s['Normal'].fontSize=9;s['Normal'].leading=13
story=[]
def p(t,style='Normal'):story.extend([Paragraph(t,s[style]),Spacer(1,7)])
def page(t):
    if story:story.append(PageBreak())
    p('BSE3227 | HVAC MINI-DESIGN | v03','Heading3');p(t,'Title')
def table(h,rs,ws):
    t=Table([h]+rs,colWidths=ws,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#153d50')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white])]))
    story.extend([t,Spacer(1,9)])
page('1. Scope and course design basis')
p('This review replaces the provisional 120 W/m2 design with the lecturer\'s Week 8 workshop basis. It covers supply diffuser selection at maximum and 40% flow, VAV grouping, flexible routes and rectangular supply duct sizing. Original architectural files are preserved.')
table(['Parameter','Adopted value','Basis'],[
['Office load area','1022 m2','Printed architectural plan'],['Total cooling allowance','189 W/m2','Workshop p.1 office row'],['Sensible heat factor','0.90','Workshop p.1 office guidance'],['Room / supply air','24 / 12 deg C','Declared design assumption'],['Ceiling height','2.7 m','Declared design assumption'],['Minimum airflow','40%','Assignment task 2'],['Course T0.25/L range','1.0-3.4','Workshop p.5 model 1400 example'],['Main / branch velocity','10 / 8 m/s maximum','Workshop p.7 office row'],['Rigid friction limit','0.8 Pa/m','Chosen within course 0.65-1.23 range'],['Rectangular aspect','No greater than 4:1','Assignment preferred limit'],['Flexible length limit','4 m','FSD 2/2023 s.7.2; brief allows 5 m']], [135,133,215])
p('Workshop: <link href="https://canvas.polyu.edu.hk/courses/5076/files/320901?module_item_id=124516" color="blue">Space air diffusion design and air duct sizing</link>. Read from Canvas PDF preview; page 5 table and example also visually checked. A local original PDF download was not obtained.')
p('<b>Course-method qualification.</b> The workshop explicitly applies the louvered 1.0-3.4 range to model 1400. Manufacturer engineering guidance instead identifies a Type 3 circular pattern. Also, the reproduced table band is 35-160 W/m2, whereas the adopted sensible allowance is 170.1 W/m2. Results here demonstrate the stated course calculation method, not measured ADPI or independent manufacturer certification. This discrepancy is retained transparently.')
p('This remains a review issue pending final drawing coordination and the remaining verification gates. It is not a construction specification or an assertion of full statutory compliance.')
page('2. Load and airflow calculations')
p(f"Total cooling = 1022 x 189 = <b>{b['total_load_kW']:.3f} kW</b>. Sensible cooling = total x 0.90 = <b>{b['sensible_load_kW']:.3f} kW</b>. These are thermal loads, not electrical power.")
p('Q = sensible load / [rho x cp x (Tr - Ts)]. Using rho = 1.2 kg/m3, cp = 1006 J/(kg K), and delta T = 12 K:')
p(f"Qmax = <b>{b['supply_lps']:.1f} L/s</b>; Qmin = 0.40 Qmax = <b>{b['minimum_supply_lps']:.1f} L/s</b>.")
p('The rectangular layout cells total 1042.10 m2, including small columns/recesses. Their relative areas allocate the given 1022 m2; the envelope is not claimed as measured net area. Each outlet airflow equals total flow times allocated area / 1022. VAV flows are sums of their four outlet flows.')
table(['VAV','Outlets','Maximum L/s','Minimum L/s'],[[v['id'],'4',f"{float(v['max_lps']):.1f}",f"{float(v['min_lps']):.1f}"] for v in vav],[105,75,150,153])
page('3. Diffuser selection and checks')
p('80 Krueger 1400/51400 four-cone diffusers are selected, with 600 x 600 mm panels and 8-inch round necks. Neck connection transitions are required from the nominal 250 mm flex. Catalogue basis: no damper, horizontal isothermal throw, B1-12 metric rows. The third throw value is T0.25.')
p('Within adjacent catalogue rows, T = T1 + (T2-T1)(Q-Q1)/(Q2-Q1). Both operating flows must lie within the tabulated range; no extrapolation is used. Static pressure and NC are approximate interpolations. A catalogue dash denotes less than NC10, not measured zero.')
p('Characteristic lengths are checked in four horizontal directions to adjacent walls or the midplane between opposing outlets. Across the open L-shaped junction, the adjacent row midplane replaces the artificial zone boundary. Reporting the smallest and largest directional T/L values makes edge conditions visible.')
p('All 80 outlets satisfy the adopted course 1.0-3.4 criterion at both maximum and 40% airflow. The highest interpolated catalogue NC is 34.9. This is a catalogue sound criterion estimate with its stated room-absorption assumption, not a prediction of installed whole-room noise.')
example=diff[0]
table(['Worked example SD-01','Maximum','40% flow'],[
['Airflow L/s',f"{float(example['max_lps']):.2f}",f"{float(example['min_lps']):.2f}"],
['T0.25 m',f"{float(example['max_T025_m']):.3f}",f"{float(example['min_T025_m']):.3f}"],
['Directional ratio minimum',f"{float(example['max_ratio_min']):.3f}",f"{float(example['min_ratio_min']):.3f}"],
['Directional ratio maximum',f"{float(example['max_ratio_max']):.3f}",f"{float(example['min_ratio_max']):.3f}"]],[223,130,130])
p('The workshop suggests 50-150 L/s as an approximate initial outlet-count guide. This is not a product rating limit: some selected outlets exceed 150 L/s, including approximately 217 L/s in the upper zone. Their throws, catalogue pressure and sound data remain within the published product range.')
p('The eight upper-zone outlets use equal spacing to remove the short opposing-jet distance that caused two candidate failures. These positions require local coordination of the 600 mm ceiling grid. Final ceiling/beam levels remain assumptions.')
page('4. VAV and flexible connections')
p('20 VAV boxes each serve four outlets. Each 1000 x 800 mm box is a schematic layout envelope, not an identified manufacturer model. Direct flexible routes include 0.50 m allowance for connections and vertical movement. Nominal flexible duct diameter is 250 mm.')
table(['VAV','Longest design flex m','Connections'],[[v['id'],f"{max(float(f['design_length_m']) for f in flex if f['vav']==v['id']):.3f}",'4'] for v in vav],[145,193,145])
p('Maximum design flex length = 2.607 m, within the adopted 4 m limit and the assignment\'s 5 m limit. Actual flex must be fully extended and installed with minimum bends; excess compression and fitting losses are not covered by the rigid straight-duct calculation.')
p('FSD Circular 2/2023 sections 7.1-7.2 govern material/test requirements and normal flex length. The AHU/corridor crossing requires a coordinated fire-enclosure and penetration-protection strategy (sections 3 and 9.2). Symbols alone do not demonstrate fire compliance.')
page('5. Supply duct sizing method')
p('The single-line tree has 49 rigid sections. Main flow starts at 12000.4 L/s; each branch carries the sum of downstream VAV maximum flows. Vertical distribution runs beside VAV envelopes, with short take-offs, rather than through boxes serving other branches.')
p('Velocity v = Q / (W x H), using actual rectangular area. Circular equivalent diameter De = 1.30(WH)^0.625/(W+H)^0.25, with dimensions in consistent units. Darcy-Weisbach friction uses De and round equivalent velocity. Assumptions: rho=1.204 kg/m3, viscosity=1.81e-5 Pa s, galvanised-sheet roughness=0.09 mm.')
p('Sizes use 50 mm increments with main/branch velocity limits 10/8 m/s, maximum friction 0.8 Pa/m and aspect ratio no greater than 4. The lowest compliant area is selected, with an aspect-ratio tie-break near 2:1. A lower achieved friction gradient is permitted where size increments or velocity govern.')
p('The MIT Serghide correlation adapted from python-hvac was checked against iterative Colebrook and five ASHRAE Table 13 reference points. The workshop supplies the ASHRAE 2013 Chapter 21 Figure 10 friction chart with density 1.20 kg/m3 and roughness 0.09 mm. Direct plotted chart-point evidence remains a final verification item; formula validation alone is not called a completed chart check.')
p('Full fitting, flexible-duct, VAV and AHU pressure losses have not been selected. This table is a straight-duct sizing calculation, not a complete fan selection. A complete system would require the critical-path loss sum and equipment pressure drops. The brief\'s required scope is supply layout and section sizing.')
page('6. Verification and references')
p('Native AutoCAD 2027 reopen confirms millimetre units and 80 two-square diffuser symbols, 20 VAV outlines, 80 flexible lines and 49 rigid section labels. The original source hashes remain unchanged. VAV and rigid-section flows reconcile with their downstream outlets. The current A1 PDF has been rendered and visually reviewed.')
p('<b>Remaining issue work:</b> finish upper-zone label coordination, complete direct friction-chart evidence, check the detailed geometry against architectural obstacles and any available marked drawing examples, and issue the final report/drawing package together. The present report does not declare those gates complete.')
for t in [
'[1] Assignment brief, tasks 1-4; supplied architectural DWG and Layout PDF.',
'[2] Lecturer Week 8, Space air diffusion design and air duct sizing, pp.1, 4-5, 7 and 9; Canvas file 320901. Ductwork design and sizing, Canvas file 320903.',
'[3] Krueger published performance B1-12; Air Distribution Engineering a1-10/a1-11. Official PDFs preserved in 02_References.',
'[4] ASHRAE Fundamentals 2021 Chapter 21, Equation 25 and Tables 12-13; Applications 2015 Chapter 57 and 2019 Chapter 58 are comparison references, not substitutes for the recorded course example.',
'[5] FSD Circular 2/2023 Mechanical Ventilating Systems, sections 3, 7.1-7.2 and 9.2.',
'[6] EMSD BEC 2024, Table 6.4 and applicable fan-power/control provisions. No full BEC compliance claim follows from these supply-only calculations.',
'[7] TomLXXVI/python-hvac, MIT, commit 94247560a667905bfbf67e45a58965a58254fce8; licence and reviewed mathematical adaptation retained.',
'Exact source URLs and version decisions: 02_References/SOURCE_REGISTER.md. All numeric schedules: 05_Calculations/data/*_v03.csv. Reproduce with build_design_v03.py, draw_review_v03.py, verify_review_v03.py and build_report_v03.py.']:p(t)
for j in range(0,len(diff),27):
    page(f'Appendix A. Diffuser schedule ({j+1}-{min(j+27,len(diff))})')
    p('All outlets: 600 mm panel / 8-inch neck. Q in L/s; T in m. Ratio ranges cover all four horizontal directions. P = pass against course 1.0-3.4 criterion, subject to Chapter 1 qualification. Full L values and pressure/NC estimates are in the CSV.')
    table(['ID','Qmax','Qmin','Tmax','Tmin','Max T/L range','Min T/L range','Check'],[[r['id'],f"{float(r['max_lps']):.1f}",f"{float(r['min_lps']):.1f}",f"{float(r['max_T025_m']):.2f}",f"{float(r['min_T025_m']):.2f}",f"{float(r['max_ratio_min']):.2f}-{float(r['max_ratio_max']):.2f}",f"{float(r['min_ratio_min']):.2f}-{float(r['min_ratio_max']):.2f}",'P'] for r in diff[j:j+27]],[48,44,44,44,44,91,91,43])
for j in range(0,len(duct),26):
    page(f'Appendix B. Duct schedule ({j+1}-{min(j+26,len(duct))})')
    table(['ID','Q L/s','W x H mm','Length m','m/s','Pa/m'],[[r['id'],f"{float(r['flow_lps']):.1f}",f"{r['width_mm']} x {r['height_mm']}",f"{float(r['length_m']):.2f}",f"{float(r['velocity_ms']):.2f}",f"{float(r['friction_Pa_m']):.3f}"] for r in duct[j:j+26]],[52,85,127,75,70,70])
def footer(c,doc):
    c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(42,25,'BSE3227 | COURSE-BASIS REVIEW v03 | 08 Nov 2026');c.drawRightString(A4[0]-42,25,str(doc.page))
out=R/'04_Final_Report/BSE3227_Design_Review_v03.pdf'
SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
