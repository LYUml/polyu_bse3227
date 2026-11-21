from pathlib import Path
import csv,json,html,sys,io,shutil
from collections import defaultdict
from reportlab.platypus import *
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing,String,Line,Rect
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.pdfgen import canvas
from pypdf import PdfWriter,PdfReader
B=Path.cwd();O=B/'05_Calculations/Grid13';src=B/'07_Agent_Work/project/course-report';sys.path.insert(0,str(src))
s=(src/'build_refined_illustrated_report.py').read_text();PUBLIC=False
def load(n):return list(csv.DictReader((O/n).open()))
term=load('Grid locations.csv');vav=load('VAV Connection Schedule.csv');duct=load('Duct Sizing.csv');rat=load('Diffuser Course Ratio Check.csv');by=defaultdict(list)
for r in rat:by[r['ID']].append(dict(r,case={'max':'maximum','min':'minimum'}[r['case']]))
def section(a,b):return s[s.index(a):s.index(b,s.index(a)+1)]
def updated(t):
 for a,b in [('24 / 12 deg C','24 / 13 deg C'),('24 - 12','24 - 13'),('12000.373','13091.316'),('4800.149','5236.526'),('2.873 m','3.083 m'),('3.373 m','3.583 m'),('0.627 m','0.417 m'),('Twelve diffusers are displaced 150 mm south within their original explicit service areas. Service-area loads, all terminal flows, VAV membership and rigid section sizes remain unchanged; Figure 2 identifies the adjusted row.','All 80 diffusers occupy distinct full ceiling tiles within their assigned service areas. Figure 2 shows the adopted arrangement. The 11 K temperature difference matches the BEC reference-building modelling basis and is adopted here as a design assumption.'),('The 320 directional lengths comprise 40 boundary-limited and 280 opposing-outlet cases.',f"The 320 directional lengths comprise {sum(r['reference']=='boundary' and r['case']=='max' for r in rat)} boundary-limited cases; the remainder terminate at opposing-outlet midplanes."),('All 640 directional operating cases lie within the adopted classroom interval T<sub>0.25</sub>/L = 1.0-3.4. Original catalogue interpolation gives 1.1526-3.0598; the independent native K-Select check gives 1.2117-3.1122 [3].','Catalogue interpolation gives 1.1608–3.4339. Minimum-flow ratios lie within the classroom interval of 1.0–3.4. At peak flow the facing outlets in Figure 3 slightly exceed the upper bound.')]:t=t.replace(a,b)
 return t
exec(updated(section('from reportlab.pdfbase import pdfmetrics',"page('3.4")))
page('3.4 Air distribution layout and local refinement')
from hvac_illustrations import overview
allocation={'terminals':[{'id':t['ID'],'center_m':[float(t['X_m']),float(t['Y_m'])]} for t in term]}
centres=json.loads((B/'07_Agent_Work/runs/course-refined-report-inputs/vav-centres.json').read_text())
d=overview(W,allocation,vav,centres,{})
for idx in reversed(range(len(d.contents))):
 item=d.contents[idx]
 if isinstance(item,String):
  if 'existing service areas' in item.text:item.text='Source plan coordinates; existing service areas and VAV group membership retained.'
  if '150 mm' in item.text:item.text='Square: grid-aligned diffuser     Blue dot: schematic VAV'
  if item.text in ('SD-56','SD-08'):del d.contents[idx-2:idx+1]
story.append(d);p('Figure 2. Grid-aligned diffuser arrangement and twenty four-outlet VAV groups.',caption)
p('Each panel occupies a full ceiling tile within its assigned service cell. Each VAV serves four outlets. The source-coordinate layout in Figure 2 defines the directional lengths in Appendix B.')
table('Table 4. Operating conditions for the adopted layout.',['Quantity','Minimum flow','Maximum flow'],[['System airflow, L/s','5236.526','13091.316'],['Sensible allowance, W/m2','68.04','170.10']],[1.8,1,1])
p('At peak flow, the ratio exceeds 3.4 by 0.0339 at the facing outlets in Figure 3. The longest conditional connection retains 0.417 m of the 4 m routing budget.',small)
page('3.5 Critical diffuser and worked calculation')
from hvac_illustrations import blue,orange
from reportlab.graphics.shapes import Polygon
d=Drawing(W,245)
scale=60
x0,y0=65,100
mid=x0+1.5*scale
for x,label in [(x0,'SD-77'),(x0+3*scale,'SD-78')]:
 d.add(Rect(x-18,y0-18,36,36,strokeColor=blue,fillColor=None))
 d.add(String(x-15,y0-34,label,fontName='Bold',fontSize=10))
d.add(Line(mid,54,mid,178,strokeColor=colors.grey,strokeDashArray=[4,3]))
d.add(String(mid+5,167,'Opposing-outlet midplane',fontName='Body',fontSize=9))
d.add(Line(x0,145,mid,145))
for x in (x0,mid):d.add(Line(x,140,x,150))
d.add(String(x0+12,151,'L = 1.5000 m',fontName='Body',fontSize=10))
end=x0+5.151*scale
d.add(Line(x0,122,end,122,strokeColor=orange,strokeWidth=1.4,strokeDashArray=[4,2]))
d.add(Polygon([end,122,end-7,125,end-7,119],fillColor=orange,strokeColor=orange))
d.add(String(end-115,130,'Isothermal throw = 5.151 m',fontName='Body',fontSize=9,fillColor=orange))
d.add(String(12,18,'Plan schematic from outlet coordinates. The dashed arrow shows catalogue isothermal throw.',fontName='Body',fontSize=8))
d.add(String(12,6,'North is upwards. The westward case at SD-78 has the same characteristic length.',fontName='Body',fontSize=8))
story.append(d)
p('Figure 3. SD-77 eastward characteristic length and tabulated isothermal throw.',caption)
p('Each diffuser supplies 202.19 L/s at peak flow. Interpolating the third isothermal throw between the 198 and 231 L/s catalogue rows gives 5.151 m. Dividing by the 1.500 m characteristic length gives 3.4339, above the classroom upper limit of 3.4. The same two outlets at 40% flow satisfy the interval.')
p('The minimum ratio occurs south of SD-60. Its 55.104 L/s minimum flow gives 2.438 m throw over a 2.100 m characteristic length, or 1.1608. The peak-flow catalogue rows bracketing SD-77/78 give NC 32 and 37. The estimated peak outlet static pressure is 30 Pa.')
sub('Worked duct-sizing check')
r=next(r for r in duct if r['ID']=='D-11')
flow,wmm,hmm,velocity=map(float,[r[k] for k in ('Q_Ls','W_mm','H_mm','V_ms')])
p(f'D-11 carries {flow:.3f} L/s through {wmm:.0f} × {hmm:.0f} mm. Area = {wmm/1000:.3f} × {hmm/1000:.3f} = {wmm*hmm/1e6:.4f} m<super>2</super>; velocity = {flow/1000:.6f}/{wmm*hmm/1e6:.4f} = {velocity:.3f} m/s, below its adopted 8 m/s branch limit. The aspect ratio is {wmm/hmm:.2f}; calculated friction is {float(r["Calc_Pa_m"]):.4f} Pa/m, below 1.23 Pa/m. These checks do not include fitting or equipment losses.')
t=updated(section("page('4. Duct","page('References'"));lines=[]
for l in t.splitlines():
 if l.startswith("p('All 47 adopted"):l="p('The revised schedule uses equivalent-round Darcy friction, 0.09 mm roughness, a 1.0 Pa/m design target and a 600 mm nominal depth cap. Appendix D and the drawing both label calculated friction.')"
 if l.startswith("p('The report, diffuser"):l="p('The grid location schedule, drawing and appendices identify the same 80 outlets and 20 groups. The appended single-line drawing includes the revised 47-section sizing schedule.')"
 if l.startswith("p('Native K-Select"):l="p('For the adopted design, the 160 operating flows are interpolated within the 33–264 L/s metric table. The manufacturer lists isothermal throw and sound under catalogue conditions. Installed noise, VAV controllability and total system pressure require separate checks.')"
 l=l.replace('All classroom directional ratio checks meet the selected interval under the stated load-range approximation.','Minimum-flow ratios meet the classroom criterion. At peak flow, SD-77 eastward and SD-78 westward slightly exceed its upper bound.')
 lines.append(l)
exec('\n'.join(lines))
sub('5.4 Governing design conditions')
table('Table 5. Worst operating cases.',['Quantity','Location','Value','Limit'],[['Highest speed','A-01–03','9.918 m/s','10 m/s'],['Highest friction','D-08','0.9995 Pa/m','1.23 Pa/m'],['Peak outlet flow','SD-77/78','202.19 L/s','Table to 264'],['Lowest ratio','SD-60 south','1.1608','1.0 min'],['Highest ratio','SD-77/78 pair','3.4339','3.4 max'],['Longest conditional flex','VAV-19','3.583 m','4.00 m']],[1.4,1.2,1,1])
page('References');refs=json.loads((src/'references-ieee.json').read_text()); original=PdfReader(B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf')
p('Reference list reproduced from the original report.')
terms={t['ID']:{'maximum_flow_L_s':float(t['Qmax_Ls']),'minimum_flow_L_s':float(t['Qmin_Ls'])} for t in term}
exec(section('for start in range(0,80,40):','for start in range(0,len(duct),24):'))
for start in range(0,len(duct),24):
 page('Appendix D. Supply duct sizing'+(' (continued)' if start else ''))
 table('Table D1. Adopted rectangular sections and calculated friction.',['Section','Flow\nL/s','Size\nmm x mm','Speed\nm/s','Limit\nm/s','Calc\nPa/m','Aspect'],[[r['ID'],f"{float(r['Q_Ls']):.2f}",r['W_mm']+' × '+r['H_mm'],f"{float(r['V_ms']):.3f}",r['Vlimit_ms'],f"{float(r['Calc_Pa_m']):.4f}",f"{float(r['W_mm'])/float(r['H_mm']):.2f}"] for r in duct[start:start+24]],[44,63,90,57,57,57,45])
tmp=O/'Restored body.pdf';SimpleDocTemplate(str(tmp),pagesize=A4,leftMargin=72,rightMargin=72,topMargin=62,bottomMargin=62).build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(tmp);assert len(reader.pages)==15,len(reader.pages)
w=PdfWriter()
for i,pg in enumerate(reader.pages):w.add_page(original.pages[7] if i==7 else pg)
w.append(str(O/'Supply Air Distribution.pdf'))
story=[]
sub('Appendix E. Manufacturer air-distribution assessment')
p('E.1 Application to the specified diffuser',heading if 'heading' in globals() else small)
p('The main design uses eighty Krueger 1400/51400 ceiling diffusers. Appendix A reports catalogue throw divided by the corresponding plan length. The manufacturer assessment examines the Type 3 circular-pattern curves in Krueger Air Distribution Engineering [4]. Each curve relates throw ratio to predicted ADPI for a specified sensible load.')
table('Table E1. Manufacturer curve selection for the adopted load assumptions.',['Condition','Sensible load','Published curves'],[['Maximum flow','170.10 W/m2','40 and 60 Btu/(h ft2)'],['40% flow','68.04 W/m2','20 and 40 Btu/(h ft2)']],[1,1,1.5])
p('The paired-curve method compares each directional ratio with both bounding load curves. A point beyond the published domain has no supported reading. The classroom assessment uses a separate ratio interval. A manufacturer ADPI pass for the adopted layout has not been established.')
sub('E.2 Linear-slot system')
p('The separate manufacturer-based system uses 63 Krueger Model 1900 linear-slot outlets. Its selection uses the Type 4 slot curves and the throw data for the selected slot configuration. The characteristic length runs in plan from the slot to the boundary or the midplane of the opposing outlet. Each outlet is checked at maximum and minimum flow.')
p('The two systems use different outlets, layouts and throw curves. Drawings and schedules in Appendices A through D apply to the 80-outlet system. Applying the slot selection at 24/13 °C requires outlet-specific flows and a fresh curve check; the existing slot study does not establish performance at that operating point.')
p('Manufacturer source: Krueger, 1900 Supply Published Performance Data, pp. 1, 4, 7 and 10. Air-distribution curves: reference [4].',small)
def appendix_footer(c,doc):
 c.setFont('Body',9);c.drawCentredString(A4[0]/2,30,'17')
appendix=io.BytesIO()
SimpleDocTemplate(appendix,pagesize=A4,leftMargin=72,rightMargin=72,topMargin=62,bottomMargin=62).build(story,onFirstPage=appendix_footer)
appendix.seek(0);w.append(PdfReader(appendix))
out=O/'BSE3227_HVAC_Design_Report.pdf';w.write(out);shutil.copy2(out,B/'00_Submit'/out.name)

