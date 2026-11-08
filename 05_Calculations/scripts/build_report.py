"""Reproducible review report; never conceal unresolved design checks."""
from pathlib import Path
import csv, json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[2]; D=R/'05_Calculations/data'
def read(name): return list(csv.DictReader((D/name).open()))
b=json.loads((D/'design_basis_v01.json').read_text())
diff=read('diffusers_v01.csv'); duct=read('ducts_v01.csv'); vav=read('vav_boxes_v01.csv'); flex=read('flex_routes_v01.csv')
audit=json.loads((D/'adpi_classification_audit_v01.json').read_text())['rows']
s=getSampleStyleSheet(); s['Normal'].fontSize=9; s['Normal'].leading=13
story=[]
def p(t,style='Normal'): story.append(Paragraph(t,s[style]));story.append(Spacer(1,7))
def title(n,t):
    if story: story.append(PageBreak())
    p('BSE3227 | HVAC MINI-DESIGN | REVIEW v01','Heading3');p(f'{n}. {t}','Title')
def table(header,rows,widths):
    t=Table([header]+rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#153d50')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('LINEBELOW',(0,0),(-1,0),.5,colors.grey)]));story.append(t)
title(1,'Scope and design basis')
p('<b>REVIEW COPY - NOT FOR SUBMISSION.</b> The native drawing, airflow allocation and duct schedule are available. Maximum-load diffuser ADPI is unresolved. This report records the current design honestly and is generated from the same data as the drawing.')
p('The assignment requires maximum and 40% airflow diffuser selection, characteristic length and ADPI checks, 4-5 diffusers per VAV box, flexible connections and a sized single-line duct network. This report documents those tasks; it does not assert that a presentation is required.')
table(['Input','Value','Evidence / status'],[
['Office load area','1022 m2','Printed source drawing label'],['External footprint','45 x 30 m','Native DWG geometry; units mm'],['Cooling allowance','120 W/m2 total','Preliminary assumption'],['Sensible heat ratio','0.75','Preliminary assumption'],['Room / supply air','24 / 12 deg C','Assumed; delta T = 12 K'],['Ceiling height','2.7 m','Assumed, requires coordination'],['Minimum airflow','40% of maximum','Assignment requirement'],['Flexible duct limit','4 m','FSD 2/2023 section 7.2'],['Rigid friction limit','0.8 Pa/m','Chosen design criterion'],['Main / branch velocity','5 / 4.5 m/s','Chosen design criteria']], [118,115,250])
p('Rectangular envelope cells total 1042.10 m2 and include columns and small recesses. Their proportions allocate the printed 1022 m2 load area; this is not a claim of measured net room area. Originals remain preserved.')
title(2,'Cooling load and air balance')
p('Total cooling = 1022 x 120 / 1000 = <b>122.64 kW</b>. Sensible cooling = 122.64 x 0.75 = <b>91.98 kW</b>. These are cooling loads, not electrical input.')
p('Supply volume = sensible heat / (air density x specific heat x temperature difference). With density 1.2 kg/m3 and specific heat 1006 J/(kg K), Q = 91980 / (1.2 x 1006 x 12) = <b>6.3494 m3/s</b> = <b>6349.4 L/s</b>. Minimum supply = <b>2539.8 L/s</b>.')
p('Each diffuser receives airflow proportional to its allocated load area. Each VAV box serves four outlets. The minimum load of 36 W/m2 sensible follows constant supply temperature and 40% airflow; it is an assumed operating model, not a measured building load.')
table(['VAV','Outlets','Maximum L/s','Minimum L/s'],[[r['id'],r['outlets'],f"{float(r['max_lps']):.1f}",f"{float(r['min_lps']):.1f}"] for r in vav],[120,80,140,143])
p('Outdoor-air requirement, return-air routing, fan selection and complete plant capacity are not proven by this supply-air balance. Occupancy and system information are needed before claiming full building-system compliance.')
title(3,'Diffuser selection and ADPI correction')
p('Selected review arrangement: 40 Krueger 1400/51400 outlets. Lower zone: 600 mm panels with 8 in necks. Upper zone: 300 mm panels with 6 in necks. Throws are linearly interpolated within the published metric rows, without extrapolation; the third catalogue throw is T0.25.')
p('<b>Classification correction:</b> the manufacturer engineering guide a1-11 identifies 1400 as Type 3 circular-pattern. The generic louvered 1.0-3.4 ratio screen in the original v01 CSV is retired as an acceptance test. For circular patterns, ASHRAE 2015 Table 3 uses distance to the closest wall or intersecting jet.')
p('At 90 W/m2 sensible, the current maximum-flow ratios fall outside both the 60 W/m2 range 0.7-1.3 and the 125 W/m2 range 0.5-1.5 in ASHRAE 2015 Table 4. Neither table gives a tested 90 W/m2 row. This is evidence to revise the design, not an exact prediction of its ADPI.')
p('At minimum load, 36 W/m2 lies between the 2019 round-diffuser 25 and 50 W/m2 cases. Comparing both tabulated envelopes is diagnostic; no measured ADPI percentage is invented. K-Select could supply more operating-point data, but its installer component was blocked by Windows Security.')
table(['Example','Q max/min L/s','Closest L m','T/L max/min'],[[diff[i]['id'],f"{float(diff[i]['max_lps']):.1f} / {float(diff[i]['min_lps']):.1f}",f"{audit[i]['L_closest_m']:.2f}",f"{audit[i]['max_T025_over_L']:.2f} / {audit[i]['min_T025_over_L']:.2f}"] for i in [0,7,31,32,39]],[90,135,110,148])
p('All 40 detailed rows are in adpi_classification_audit_v01.json and diffusers_v01.csv. Current release status remains NOT ACCEPTED. Geometry, neck size and operating assumptions must be reconsidered with applicable performance evidence before final issue.')
title(4,'VAV layout and flexible connections')
p('Ten VAV boxes serve four outlets each. Their 1000 x 800 mm plan envelopes are schematic allowances, not manufacturer-selected equipment dimensions. Flexible routes run directly from box corners to outlets; the calculated route adds 0.5 m for connection/drop allowance.')
table(['VAV','Longest design flex m','Connections','Limit check'],[[r['id'],f"{max(float(f['design_length_m']) for f in flex if f['vav']==r['id']):.3f}",'4','Within 4 m'] for r in vav],[120,150,100,113])
p('Maximum flexible design length is 3.473 m. Lower-zone flex is nominal 250 mm; upper-zone flex is 200 mm. Product-specific flexible-duct pressure losses, actual bends and reducer losses are not included in the straight rigid-duct friction schedule.')
p('FSD Circular 2/2023 section 7.1 specifies flexible-duct material/test requirements and section 7.2 normally limits length to 4 m. Fire-compartment penetrations and the AHU/corridor crossing require a coordinated fire strategy. Section 9.2 protected-area requirements cannot be satisfied merely by drawing a fire-damper symbol.')
title(5,'Rigid duct sizing schedule')
p('Rectangular velocity uses actual area: v = Q/(W x H). Equal-friction equivalent diameter: De = 1.30(WH)^0.625/(W+H)^0.25. Darcy-Weisbach uses standard-air density 1.204 kg/m3, viscosity 1.81e-5 Pa s and assumed roughness 0.09 mm. Sizes use 50 mm increments and aspect ratio no greater than 4.')
p('The reviewed MIT Serghide correlation from python-hvac is checked against iterative Colebrook and five ASHRAE Table 13 points. These checks validate the implementation; they do not replace fitting-loss or full fan-pressure calculations.')
table(['Section','L/s','W x H mm','m/s','Pa/m'],[[r['id'],f"{float(r['flow_lps']):.1f}",f"{r['width_mm']} x {r['height_mm']}",f"{float(r['velocity_ms']):.2f}",f"{float(r['friction_Pa_m']):.3f}"] for r in duct],[80,90,133,80,100])
title(6,'Verification and reference trail')
p('Completed evidence: native AutoCAD 2027 source inspection (INSUNITS=4); a three-diffuser placement/plot sample; native review DWG save and reopen; review PDF inspection; 40 outlets / 10 VAVs / 40 flex routes; source hashes preserved; reproducible air balance and straight-duct sizing.')
p('<b>Remaining acceptance work:</b> resolve maximum/minimum diffuser ADPI with the correct pattern and applicable load evidence; revise layout/selection as necessary; label all short duct sections legibly; complete friction-chart evidence; regenerate and inspect final drawing sheets; reconcile every final schedule and drawing count. No final release is claimed.')
p('EMSD BEC 2024 Table 6.4 is a load-design-condition reference, not a prescribed W/m2 allowance. VAV fan power and static-pressure control provisions require system evidence. BEC water-pipe friction provisions are not air-duct friction limits.')
for t in [
'[1] BSE3227 Mini design assignment, pp. 1-2, tasks 1-4; supplied Project layout.dwg and Layout.pdf.',
'[2] Krueger 1400/51400 published performance, B1-11/B1-12; Air Distribution Engineering a1-10/a1-11; Reference Charts B1-10. Official downloads are preserved in 02_References.',
'[3] ASHRAE Applications 2015, Chapter 57 Tables 3-4; Applications 2019, Chapter 58 Tables 5-6A. Official handbook HTML snapshots are preserved.',
'[4] ASHRAE Fundamentals 2021, Chapter 21, Figure 10, Equation 25, Tables 12-13.',
'[5] EMSD Building Energy Code 2024, Table 6.4; sections 6.7.2-6.7.5 and 6.10.6.1-2.',
'[6] Hong Kong FSD Circular 2/2023, Mechanical Ventilating Systems: sections 3, 7.1-7.2 and 9.2.',
'[7] Liu, Clark and Novoselac (2017), Energy and Buildings 134, 271-284. The supplied paper tests 25/50 W/m2; it does not prescribe this office load.',
'[8] TomLXXVI/python-hvac, MIT, pinned commit 94247560a667905bfbf67e45a58965a58254fce8. See 06_Tools/TOOL_REVIEW.md and preserved licence.']: p(t)
p('Exact URLs, source locators and assumptions: 02_References/SOURCE_REGISTER.md. Calculation inputs and audit records: 05_Calculations/data. This report is reproducible with build_report.py.')
def footer(c,doc):
    c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(42,25,'BSE3227 | REVIEW ONLY | 08 Nov 2026');c.drawRightString(A4[0]-42,25,str(doc.page))
out=R/'04_Final_Report/BSE3227_Design_Review_v01.pdf'
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=35,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)

