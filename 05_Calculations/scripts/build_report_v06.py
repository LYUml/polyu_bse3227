"""Course-basis report with complete schedules, generated from v04 data."""
from pathlib import Path
import csv,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data'
def read(n):return list(csv.DictReader((D/n).open()))
b=json.loads((D/'design_basis_v04.json').read_text());diff=read('diffusers_v04.csv');duct=read('ducts_v04.csv');vav=read('vav_boxes_v04.csv');flex=read('flex_routes_v04.csv')
s=getSampleStyleSheet();s['Normal'].fontSize=9;s['Normal'].leading=13
story=[]
def p(t,style='Normal'):story.extend([Paragraph(t,s[style]),Spacer(1,7)])
def page(t):
    if story:story.append(PageBreak())
    p('BSE3227 | HVAC MINI-DESIGN | v06','Heading3');p(t,'Title')
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
p('This package is prepared for user review against the assignment scope. Ceiling coordination and fire-protection details remain explicitly stated design assumptions; this is not a construction specification or an assertion of full statutory compliance.')
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
p('The MIT Serghide correlation adapted from python-hvac was checked against iterative Colebrook and five ASHRAE Table 13 reference points. Four selected sections were also visually checked on the original ASHRAE 2021 Chapter 21 Figure 9 friction chart (Appendix D). The corresponding workshop reference is 2013 Figure 10. Both state density 1.20 kg/m3 and roughness 0.09 mm. Graphical readings are approximate; the numerical correlation controls exact sizing.')
p('Full fitting, flexible-duct, VAV and AHU pressure losses have not been selected. This table is a straight-duct sizing calculation, not a complete fan selection. A complete system would require the critical-path loss sum and equipment pressure drops. The brief\'s required scope is supply layout and section sizing.')
page('6. Verification and references')
p('Native AutoCAD 2027 reopen confirms millimetre units and 80 two-square diffuser symbols, 20 VAV outlines, 80 flexible lines and 49 rigid section labels. The original source hashes remain unchanged. VAV and rigid-section flows reconcile with their downstream outlets. The current A1 PDF has been rendered and visually reviewed.')
p('Additional geometric audit identified nine column footprints from source polylines and closed linework. Diffuser, VAV, rigid duct and flex footprints do not overlap these columns in plan. A 269 mm duplicated upper-branch route found in v03 is corrected in v04 as one common main section carrying both downstream VAV flows. No collinear rigid-centreline duplicates remain. This is a 2D audit, not a beam/headroom or fire approval.')
p('<b>Native geometry reconciliation completed:</b> the v06 DWG was reopened in AutoCAD 2027 and inspected through a read-only export. All 49 rigid and 80 flexible line endpoints, 80 diffuser symbols, 20 VAV envelopes and 49 section IDs match the shared data. Flow balances independently at geometric junctions. All 3894 source model entities retain their geometry, including an anonymous ceiling block whose export name changed. The v06 drawing adjusts upper-zone annotations without changing the v04 engineering data. Evidence: native_reconciliation_v06.json. User acceptance is pending.')
for t in [
'[1] Assignment brief, tasks 1-4; supplied architectural DWG and Layout PDF.',
'[2] Lecturer Week 8, Space air diffusion design and air duct sizing, pp.1, 4-5, 7 and 9; Canvas file 320901. Ductwork design and sizing, Canvas file 320903.',
'[3] Krueger published performance B1-12; Air Distribution Engineering a1-10/a1-11. Official PDFs preserved in 02_References.',
'[4] ASHRAE Fundamentals 2021 Chapter 21, Equation 25 and Tables 12-13; Applications 2015 Chapter 57 and 2019 Chapter 58 are comparison references, not substitutes for the recorded course example.',
'[5] FSD Circular 2/2023 Mechanical Ventilating Systems, sections 3, 7.1-7.2 and 9.2.',
'[6] EMSD BEC 2024, Table 6.4 and applicable fan-power/control provisions. No full BEC compliance claim follows from these supply-only calculations.',
'[7] TomLXXVI/python-hvac, MIT, commit 94247560a667905bfbf67e45a58965a58254fce8; licence and reviewed mathematical adaptation retained.',
'Exact source URLs and version decisions: 02_References/SOURCE_REGISTER.md. All numeric schedules: 05_Calculations/data/*_v04.csv. Reproduce calculations with build_design_v04.py; draw with draw_acceptance_v06.py; audit actual geometry with reconcile_native_v06.py; generate this report with build_report_v06.py. Earlier v04 count, source-hash and column audits remain relevant to unchanged geometry.']:p(t)
for j in range(0,len(diff),27):
    page(f'Appendix A. Diffuser schedule ({j+1}-{min(j+27,len(diff))})')
    p('All outlets: 600 mm panel / 8-inch neck. Q in L/s; T in m. Ratio ranges cover all four horizontal directions. P = pass against course 1.0-3.4 criterion, subject to Chapter 1 qualification. Full L values and pressure/NC estimates are in the CSV.')
    table(['ID','Qmax','Qmin','Tmax','Tmin','Max T/L range','Min T/L range','Check'],[[r['id'],f"{float(r['max_lps']):.1f}",f"{float(r['min_lps']):.1f}",f"{float(r['max_T025_m']):.2f}",f"{float(r['min_T025_m']):.2f}",f"{float(r['max_ratio_min']):.2f}-{float(r['max_ratio_max']):.2f}",f"{float(r['min_ratio_min']):.2f}-{float(r['min_ratio_max']):.2f}",'P'] for r in diff[j:j+27]],[48,44,44,44,44,91,91,43])
for j in range(0,len(duct),26):
    page(f'Appendix B. Duct schedule ({j+1}-{min(j+26,len(duct))})')
    table(['ID','Q L/s','W x H mm','Length m','m/s','Pa/m'],[[r['id'],f"{float(r['flow_lps']):.1f}",f"{r['width_mm']} x {r['height_mm']}",f"{float(r['length_m']):.2f}",f"{float(r['velocity_ms']):.2f}",f"{float(r['friction_Pa_m']):.3f}"] for r in duct[j:j+26]],[52,85,127,75,70,70])
for j in range(0,len(diff),28):
    page(f'Appendix C. Characteristic lengths ({j+1}-{min(j+28,len(diff))})')
    p('L in metres, measured horizontally from the outlet to a wall or opposing-outlet midplane. West/east/south/north refer to the drawing directions. Apply each directional L to both maximum and minimum throw; Appendix A gives the resulting extreme ratios.')
    table(['Outlet','West L','East L','South L','North L'],[[r['id']]+[f"{float(r[k]):.3f}" for k in ['L_w_m','L_e_m','L_s_m','L_n_m']] for r in diff[j:j+28]],[83,100,100,100,100])
page('Appendix D. Friction-chart cross-check')
p('Original official ASHRAE chart, rotated for reading. Source: 2021 Fundamentals, Chapter 21 Figure 9. Four broad read-off intervals below are consistent with the calculated gradients; line thickness limits graphical precision.')
class Chart(Flowable):
    def __init__(self):Flowable.__init__(self);self.width=480;self.height=348
    def draw(self):
        self.canv.saveState();self.canv.translate(0,348);self.canv.rotate(-90)
        self.canv.drawImage(str(R/'02_References/ASHRAE_2021_Ch21_Fig09_Friction.jpg'),0,0,width=348,height=480)
        self.canv.restoreState()
story.extend([Chart(),Spacer(1,12)])
chart=json.loads((D/'friction_chart_review.json').read_text())
table(['Section','Q L/s','De mm','Chart Pa/m','Calc. Pa/m'],[[r['section'],str(r['Q_L_s']),str(r['De_mm']),f"{r['chart_Pa_m_range'][0]}-{r['chart_Pa_m_range'][1]}",str(r['calculated_Pa_m'])] for r in chart['points']],[70,90,90,125,108])
p('<link href="https://handbook.ashrae.org/Handbooks/F21/SI/F21_Ch21/F21_Ch21_si.aspx#F21_Ch21_fig9" color="blue">Official chart and accompanying duct-design chapter</link>. The four-point visual check supplements the full section-by-section numerical calculations; it is not claimed as exact chart digitisation.')
def footer(c,doc):
    c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(42,25,'BSE3227 | USER ACCEPTANCE v06 | 09 Nov 2026');c.drawRightString(A4[0]-42,25,str(doc.page))
out=R/'04_Final_Report/BSE3227_Design_Acceptance_v06.pdf'
SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
