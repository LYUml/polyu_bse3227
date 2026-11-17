"""Append a clearly separated, unadopted comparison to the preserved course report."""
from pathlib import Path
import csv,json,hashlib,html
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader,PdfWriter
from hvac_illustrations import critical_detail

B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work'
R=P/'runs/course-sourced-load-candidate';O=P/'runs/course-report-supplementary-load';O.mkdir(exist_ok=False)
base=B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={k:sha(p) for k,p in dict(baseline=base,allocation=R/'allocation.json',native=R/'Native K-Select Check.json',online=R/'Online Ductulator Check.json',ducts=R/'schedule-corridor/schedule.csv',source=P/'project/adpi-source-review/HKIE Office Cooling Load.pdf').items()}
assert inputs['baseline']=='0492f0fe98e926f75bc84973cbd956daadc6c2e0f7e21533f2af1c5c33aad09a'
n=json.loads((R/'Native K-Select Check.json').read_text());web=json.loads((R/'Online Ductulator Check.json').read_text())
allocation=json.loads((R/'allocation.json').read_text());summary=json.loads((R/'review-native.json').read_text())
assert n['independent_all_table_checks_pass'] and n['all640_reported_native_ratios_within_classroom_interval']
assert web['all47_displayed_friction_below_source_caps_including_half_last_digit']
for alias,name in [('Body','times.ttf'),('Bold','timesbd.ttf'),('Italic','timesi.ttf')]:pdfmetrics.registerFont(TTFont(alias,'C:/Windows/Fonts/'+name))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
W=A4[0]-144;story=[]
body=ParagraphStyle('Body',fontName='Body',fontSize=12,leading=15,alignment=TA_JUSTIFY,spaceAfter=8)
head=ParagraphStyle('Heading',parent=body,fontName='Bold',fontSize=15,leading=19,spaceAfter=12,alignment=0)
sub=ParagraphStyle('Sub',parent=body,fontName='Bold',spaceBefore=5,spaceAfter=6,alignment=0)
small=ParagraphStyle('Small',parent=body,fontSize=10,leading=12,alignment=0,spaceAfter=6)
def p(s,style=body):story.append(Paragraph(s,style))
def table(title,rows):
 p(title,sub)
 data=[[Paragraph(html.escape(str(v)),small) for v in row] for row in rows]
 t=Table(data,colWidths=[W*.42,W*.29,W*.29],repeatRows=1)
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEABOVE',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.7,colors.black),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]));story.extend([t,Spacer(1,8)])
def footer(c,d):c.setFont('Body',9);c.drawCentredString(A4[0]/2,34,str(16+d.page))

p('Appendix E. Supplementary load-basis comparison',head)
p('E.1 Purpose and status',sub)
p('The main coursework design, drawings and schedules retain the 189 W/m<super>2</super> classroom allowance, 0.90 sensible factor and specified 1400/51400 family. The assignment requests a rule-of-thumb load; the classroom guide offers 189 W/m<super>2</super> as a preliminary reference. This appendix examines another explicit assumption. It does not replace the main design or remove its ADPI applicability limitation.')
p('A Hong Kong office study reports a whole-floor cooling load of 129 W/m<super>2</super>, excluding safety/standby allowance [7]. Applying a declared 15% design margin gives 148.35 W/m<super>2</super>, rounded upward to 150 W/m<super>2</super>. This is a coursework scenario, not a measured load for this building. The study concerns one office floor with 1999 measurements; its 2001 publication does not establish a universal or current design allowance.')
table('Table E1. Consistent main and supplementary assumptions.',[
 ['Quantity','Main coursework','Supplement only'],
 ['Total / sensible allowance, W/m2','189 / 170.1','150 / 135'],
 ['Total / sensible cooling, kW thermal','193.158 / 173.842','153.300 / 137.970'],
 ['Maximum / minimum airflow, L/s','12000.373 / 4800.149','9524.105 / 3809.642'],
 ['600 x 600 mm panel neck','8 inch','6 inch'],
 ['Outlets / VAV groups / rigid sections','80 / 20 / 47','80 / 20 / 47'],
 ['Native 640-case T0.25/L range','1.2117-3.1122','1.0771-2.6973'],
 ['Sensible table range, 35-160 W/m2','Maximum outside','135 max / 54 min inside'],
 ])
p('The supplementary scenario retains every diffuser position, service cell, VAV membership and rigid route. All 47 rectangular sizes are recalculated within the original per-section velocity, friction and aspect limits, with neither width nor height increased. Actual Online Ductulator checks cover all 47 sections through 36 unique inputs; the largest displayed friction is 1.200 Pa/m. These are section-sizing results, not a complete system pressure or fan selection.',small)

story.append(PageBreak());p('E.2 Air-diffusion checks and interpretation',head)
p('The classroom louvered-ceiling method uses T<sub>0.25</sub>/L = 1.0-3.4 over 35-160 W/m<super>2</super> [8]. With the supplementary assumptions, all 640 original-catalogue checks pass (1.0909-2.7273). All 640 native K-Select checks also pass (1.0771-2.6973): 48 distinct whole-CFM reports were reconciled through 2,352 independent scalar checks. Maximum input rounding is 0.2248 L/s. Neither result is a measured ADPI percentage.')
position=json.loads((P/'runs/course-diffuser-position-screen/axis1_-0.15.json').read_text());critical=n['maximum_case']
case=next(v for v in position['cases'] if v['terminal']==critical['terminal'] and v['direction']==critical['direction'])
d=critical_detail(W,allocation,case,critical);d.height=220;story.append(d)
p('Figure E1. Supplementary SD-50 northward geometry and native tabulated throw. The dashed arrow represents isothermal catalogue throw, not a simulated jet.',ParagraphStyle('Caption',parent=small,fontName='Italic',alignment=TA_CENTER))
p('At SD-50 maximum flow, 117.319 L/s rounds to 249 CFM. Native throw is 13 ft = 3.9624 m; L = 1.469042 m, giving 2.6973. The lower native extreme is SD-08 eastward at minimum flow: 8 ft / 2.263959 m = 1.0771. The manufacturer Type 3 circular-pattern ADPI curves remain a different method and are not declared satisfied. A 40% flow case assumes proportional sensible duty; it is a preliminary operating scenario, not a room-control simulation.',small)
p('Additional references',sub)
refstyle=ParagraphStyle('Reference',parent=small,leftIndent=24,firstLineIndent=-24,splitLongWords=True)
p('[7] S. T. H. Lao and S. Deng, "An evaluation of the rules of thumb for estimating cooling load for office buildings," <i>HKIE Transactions</i>, vol. 8, no. 3, pp. 58-59, 2001, doi: 10.1080/1023697X.2001.10667859.',refstyle)
url='https://handbook.ashrae.org/Handbooks/A15/SI/a15_ch57/a15_ch57_si.aspx'
p('[8] ASHRAE, "Room air distribution," <i>ASHRAE Handbook Online</i>, Table 3. Accessed: Nov. 17, 2026. [Online]. Available: <link href="'+url+'">'+url+'</link>.',refstyle)
appendix=O/'Supplementary Load Comparison.pdf';SimpleDocTemplate(str(appendix),pagesize=A4,leftMargin=72,rightMargin=72,topMargin=62,bottomMargin=62).build(story,onFirstPage=footer,onLaterPages=footer)
assert len(PdfReader(appendix).pages)==2
w=PdfWriter();w.append(base);w.append(appendix);out=O/'BSE3227 HVAC Mini-Design.pdf'
with out.open('wb') as f:w.write(f)
assert sha(base)==inputs['baseline']
review=dict(scope='Main189W/m2 coursework preserved; unadopted150W/m2 alternative only in Appendix E under explicit user instruction',inputs=inputs,main_pages_preserved=16,appendix_pages=2,total_pages=18,report_sha256=sha(out),main_design_changed=False,alternative_adopted=False,manufacturer_ADPI_accepted=False,physical_ADPI_verified=False,user_accepted=False,visual_review='pending')
(O/'review.json').write_text(json.dumps(review,indent=2));print(json.dumps(review,indent=2))
