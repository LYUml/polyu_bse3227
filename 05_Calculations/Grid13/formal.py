from pathlib import Path
import csv,json,shutil,html
from collections import defaultdict
from reportlab.platypus import *
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from pypdf import PdfReader,PdfWriter
B=Path.cwd(); O=B/'05_Calculations/Grid13'
template=(B/'07_Agent_Work/project/course-report/build_bse3125_style_report.py').read_text()
exec(template[template.index('from reportlab.pdfbase import pdfmetrics'):template.index("p('1. Introduction")])
members=json.loads((B/'07_Agent_Work/project/course-report/Private/group-details.json').read_text())['members']
p(' &nbsp; '.join(x['name']+' '+x['student_id'] for x in members),caption)
def load(name):return list(csv.DictReader((O/name).open()))
term=load('Grid locations.csv');rat=load('Diffuser Course Ratio Check.csv');duct=load('Duct Sizing.csv');vav=load('VAV Connection Schedule.csv');by=defaultdict(list)
for r in rat:by[r['ID']].append(dict(r,case={'max':'maximum','min':'minimum'}[r['case']]))
p('1. Introduction and design basis',heading);sub('1.1 Design objective');p('The variable air volume system serves the open-plan office. This design sizes the supply ductwork and evaluates diffuser throw at peak load and at 40% airflow.')
sub('1.2 Adopted office and system assumptions');table('Table 1. Principal design inputs.',['Parameter','Adopted value'],[['Office load area','1,022 m²'],['Total cooling allowance / sensible factor','189 W/m² / 0.90'],['Room / supply air temperature','24 / 13 °C'],['Density / specific heat','1.20 kg/m³ / 1,006 J/(kg K)'],['Diffuser','Krueger 1400/51400, 600 mm face, 8-inch neck'],['Distribution','80 diffusers, 20 VAV groups, 47 rigid sections']],[1,1.45])
p('The 13 °C supply temperature follows the typical all-air design described by ASHRAE [3]. The resulting 11 K difference also matches the reference-building modelling assumption in BEC 2024 Appendix A [4].')
page('2. Cooling load, airflow and VAV layout');sub('2.1 Preliminary thermal balance');table('Table 2. Cooling load and airflow.',['Calculation','Result'],[['1,022 × 189 W/m²','193.158 kW total'],['193.158 × 0.90','173.842 kW sensible'],['173,842 / (1.20 × 1,006 × 11)','13,091.3 L/s maximum'],['0.40 × maximum','5,236.5 L/s minimum']],[1.5,1])
sub('2.2 Ceiling coordination and VAV connections');p('Each square panel is centred on a distinct complete 600 × 600 mm tile inside its assigned service area. The existing area-based allocation determines the share of flow. Each VAV box serves four outlets. Appendix C gives the group totals and connection lengths.')
p('The longest straight plan connection measures 3.083 m. The 0.50 m allowance for vertical travel and slack gives 3.583 m against the adopted 4.00 m design cap. Installed lengths depend on box elevation, bend radii and final routing.')
page('3. Diffuser selection and air-diffusion checks');p('The metric no-damper performance table [2] covers 33–264 L/s. Linear interpolation of its third isothermal throw supplies T0.25. In each cardinal direction, L extends to the first boundary or the midplane of an aligned opposing outlet, whichever is closer.')
exec(template[template.index('d=Drawing(W,165)'):template.index("sub('3.3 Interpretation")])
sub('3.1 Governing pair');p('SD-77 east and SD-78 west each carry 202.19 L/s at peak. The opposing outlet centres are 3.00 m apart, giving L = 1.50 m. The catalogue throw of 5.151 m gives T/L = 3.434. These two directions exceed 3.4. The remaining 318 peak cases and all 320 minimum cases fall within the classroom interval.')
p('The peak outlet lies between catalogue rows at 198 and 231 L/s, with NC 32 and NC 37 respectively. Interpolated static pressure is about 30 Pa. The sensible duty of 170.1 W/m² exceeds the classroom table limit of 160 W/m², so the exercise cannot establish ADPI ≥80%.')
page('4. Duct sizing and governing conditions');p('Rectangular sections use 50 mm size increments, a nominal depth cap of 600 mm, aspect ratio up to 4 and a design friction target of 1.0 Pa/m. The calculation uses equivalent round diameter, Darcy friction and 0.09 mm roughness. Beam clearance, insulation and available width require coordination.')
table('Table 3. Governing design conditions.',['Check','Location','Result','Criterion'],[['Highest velocity','A-01 to A-03','9.918 m/s','10 m/s'],['Highest friction','D-08','0.9995 Pa/m','1.23 Pa/m'],['Highest outlet flow','SD-77 / SD-78','202.19 L/s','Catalogue to 264 L/s'],['Minimum T/L','SD-60 south','1.1608','≥1.0'],['Maximum T/L','SD-77 east / SD-78 west','3.4339','≤3.4'],['Longest flex incl. allowance',max(vav,key=lambda x:float(x['Max plan m']))['VAV'],'3.583 m','4.00 m']],[1.3,1.35,1,1])
sub('4.1 Design assessment');p('All 47 sections meet the selected velocity and friction limits. A-01 carries 13.091 m³/s through a 2.20 × 0.60 m section. The remaining diffuser issue is concentrated at the SD-77/78 pair. VAV minimum controllable flow, pressure differential and sound require equipment selection at the group flows in Appendix C.')
page('References')
for x in ['[1] BSE3227 HVACR 1. Mini-design assignment and Space air diffusion design and air duct sizing, pp. 1, 4–5, 7 and 9.','[2] Krueger. Louvered Face Diffusers, 1400/51400 Series, four-cone performance, metric no-damper tables B1-11/12.','[3] ASHRAE. HVAC Systems and Equipment Handbook, Air Handling and Distribution.','[4] Electrical and Mechanical Services Department. Code of Practice for Energy Efficiency of Building Services Installation, 2024, Appendix A.','[5] Krueger. SDIOM, Table 6.A, basic unit with damper fully open.']:p(x)
for offset in (0,40):
 page('Appendix A. Diffuser operating schedule');table('Table A1. Catalogue flow and directional extremes.',['Outlet','Max L/s','Min L/s','Tmax m','Tmin m','Upper T/L','Lower T/L'],[[t['ID'],f"{float(t['Qmax_Ls']):.2f}",f"{float(t['Qmin_Ls']):.2f}",*[f'{f:.3f}' for f in [max(float(r['T025_m']) for r in by[t['ID']]),min(float(r['T025_m']) for r in by[t['ID']]),max(float(r['ratio']) for r in by[t['ID']]),min(float(r['ratio']) for r in by[t['ID']])]]] for t in term[offset:offset+40]],[1]*7)
for offset in (0,40):
 page('Appendix B. Characteristic lengths');table('Table B1. Plan directional lengths in metres.',['Outlet','West','East','South','North'],[[t['ID']]+[f"{float(next(r['L_m'] for r in by[t['ID']] if r['direction']==d)):.4f}" for d in ['west','east','south','north']] for t in term[offset:offset+40]],[1]*5)
page('Appendix C. VAV grouping and connections');table('Table C1. Group airflow and planar connection range.',['VAV','Diffuser outlets','Max L/s','Min L/s','XY range m'],[[g['VAV'],g['Diffuser outlets'],g['Qmax L/s'],g['Qmin L/s'],g['Min plan m']+'–'+g['Max plan m']] for g in vav],[1,3,1,1,1.5])
for n in (0,24):
 page('Appendix D. Supply duct sizing');table('Table D1. Adopted rectangular sections and calculated friction.',['Section','Flow L/s','Size mm','Speed m/s','Limit m/s','Calc Pa/m','Aspect'],[[r['ID'],f"{float(r['Q_Ls']):.1f}",r['W_mm']+' × '+r['H_mm'],f"{float(r['V_ms']):.3f}",r['Vlimit_ms'],f"{float(r['Calc_Pa_m']):.4f}",f"{float(r['W_mm'])/float(r['H_mm']):.2f}"] for r in duct[n:n+24]],[1,1,1.4,1,1,1,0.8])
bodypdf=O/'body.pdf';SimpleDocTemplate(str(bodypdf),pagesize=A4,leftMargin=66,rightMargin=66,topMargin=58,bottomMargin=50).build(story,onFirstPage=footer,onLaterPages=footer)
writer=PdfWriter()
for f in [bodypdf,O/'Supply Air Distribution.pdf',O/'VAV Connection Schedule.pdf']:writer.append(str(f))
out=O/'BSE3227_HVAC_Design_Report.pdf';writer.write(out);shutil.copy2(out,B/'00_Submit'/out.name)


