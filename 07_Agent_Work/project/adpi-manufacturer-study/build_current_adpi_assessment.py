"""Course-basis decision artifact; does not replace the formal design/report."""
import json,hashlib
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing,Line,String
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/adpi-current-assessment-labelled';R.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());current=read(P/'runs/adpi-current-all-panels/review.json');slot=read(P/'runs/adpi-existing-slot-margin-review/review.json')
curves=read(P/'runs/manufacturer-adpi-native-curves/curves.json')
for name,font in [('Body','times.ttf'),('Bold','timesbd.ttf'),('Italic','timesi.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+font))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
body=ParagraphStyle('Body',fontName='Body',fontSize=11,leading=14,spaceAfter=8)
heading=ParagraphStyle('Heading',parent=body,fontName='Bold',fontSize=16,leading=20,spaceAfter=12)
small=ParagraphStyle('Small',parent=body,fontSize=9,leading=11,spaceAfter=6)
story=[];W=A4[0]-120
def p(text,style=body):story.append(Paragraph(text,style))
def table(rows,widths):
    t=Table([[Paragraph(str(c),small) for c in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEBELOW',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black)]));story.extend([t,Spacer(1,10)])
p('BSE3227: ADPI Design Assessment',heading)
p('1. Current prescribed Model 1400 scheme',heading)
p('The adopted coursework scheme retains 80 diffusers, 20 VAV groups and 47 rigid sections. The given preliminary load basis is retained: 189 x 0.90 = 170.1 W/m<super>2</super>. Maximum and minimum flows remain 12000.373 and 4800.149 L/s. No load number is reduced to obtain a pass.')
p('The existing classroom ratio check passes 640/640 cases using 1.0-3.4, but this does not establish an applicable ADPI prediction at 170.1 W/m<super>2</super>. The manufacturer identifies Model 1400 with the Type 3 circular pattern, which has a different source-curve envelope [1].')
table([['Executed comparison','Result'],['Current geometry checked against original directional lengths','320/320 match'],['Published Model 1400 panel/neck combinations','8 (300 mm and 600 mm panels)'],['Terminal / specification comparisons','640'],['Individual source-curve checks','7704'],['Terminals with any option passing every paired-curve check','0/80']],[W*.68,W*.32])
d=Drawing(W,175);x0=32;y0=35;cw=W-48;ch=117
X=lambda x:x0+x/3.4*cw;Y=lambda y:y0+(y-60)/40*ch
d.add(String(x0,164,'ADPI (%) - published source curves',fontName='Body',fontSize=8))
d.add(String(W/2-12,23,'T50/L',fontName='Body',fontSize=8))
for y in [60,70,80,90,100]:
    d.add(Line(x0,Y(y),W-10,Y(y),strokeColor=colors.lightgrey,strokeWidth=.4));d.add(String(8,Y(y)-3,str(y),fontName='Body',fontSize=8))
for x in [0,1,2,3]:d.add(String(X(x),y0-12,str(x),fontName='Body',fontSize=8))
for fragment in curves['fragments']:
    if fragment['load_Btuh_ft2'] not in [40,60]:continue
    color=colors.black if fragment['load_Btuh_ft2']==60 else colors.grey
    for a,b in zip(fragment['points'],fragment['points'][1:]):d.add(Line(X(a[0]),Y(a[1]),X(b[0]),Y(b[1]),strokeColor=color,strokeWidth=1))
d.add(Line(x0,Y(80),W-10,Y(80),strokeColor=colors.HexColor('#A94027'),strokeWidth=.8,strokeDashArray=[4,3]))
d.add(String(X(2),Y(95),'Black: 60; grey: 40 Btuh/ft2',fontName='Body',fontSize=8))
d.add(Line(X(1.2116829211),12,X(3.1122323256),12,strokeColor=colors.HexColor('#206887'),strokeWidth=3))
d.add(String(32,0,'Blue bar: current native T/L range, both cases; no ADPI assigned to this bar.',fontName='Body',fontSize=8))
story.append(d);p('Figure 1. Published Type 3 source curves and the current geometric ratio range [1].',small)
p('All eight panel/neck tables come from the prescribed original performance data [2]. No suitable option was found for the unchanged layout under this diagnostic. This is not proof that every possible redesign is infeasible. Published curve limits, fragment gaps and catalogue flow exclusions are retained as unknown/excluded values, not assigned an ADPI of zero.',small)
story.append(PageBreak());p('2. Existing manufacturer comparison and decision',heading)
p('A separate, already developed 63-outlet Model 1900 linear-slot comparison is preserved [3]. A fresh readback checks the same selected specifications, source geometry, explicit service areas and flows. No optimizer or native drawing generator is rerun for this check.')
table([['Comparison check','Result'],['Existing selected linear-slot outlets','63'],['Source event / load / operating checks','1624'],['Paired published-curve checks at the 80 threshold','All pass'],['Lowest source-curve reading after digitized stroke allowance','80.08 (graph representation only)'],['Added ceiling-to-occupied-zone distance','None; planar L used']],[W*.68,W*.32])
p('ASHRAE Table 5 defines ceiling-slot L using the wall or outlet midplane; it lists the additional ceiling/occupied-zone distance separately for light troffers [4]. The fresh comparison therefore adds no hypothetical downward travel. Because the interpreted boundary is axis-aligned, every boundary vertex and opposing finite-slot endpoint partitions the two-dimensional ray geometry into constant-length intervals.')
p('The maximum-load comparisons use both 40 and 60 Btuh/ft<super>2</super> curves; minimum-load comparisons use both 20 and 40. Passing both bounding source curves is a declared selection diagnostic, not proof of intermediate-load monotonicity, an exact 170.1 W/m<super>2</super> ADPI value, or measured occupied-zone performance. The result has little source-curve margin and should not be described as comfortably above 80%.')
p('The key coursework constraint remains: the brief specifies Model 1400/51400; Model 1900 cannot silently replace it. Manufacturer comparison work can be included as an alternative, but it does not clear the specified-product obligation. The formal 16-page coursework package is preserved while this design-basis decision is made.')
p('References',heading)
for text in [
 '[1] Krueger, "Air distribution engineering," 2012, pp. a1-10-a1-11. [Online]. Available: https://www.krueger-hvac.com/file/9261/GRD_Engineering.pdf',
 '[2] Krueger, "1400, 51400, M1400, M51400 published performance data," 2012, pp. B1-11-B1-12. [Online]. Available: https://www.krueger-hvac.com/file/3118/1400_51400_M1400_M51400_PublishedPerformanceData.pdf',
 '[3] Krueger, "1900 supply published performance data," pp. 1, 4, 7, 10. [Online]. Available: https://www.krueger-hvac.com/file/6830/1900_Supply_PublishedPerformanceData.pdf',
 '[4] ASHRAE, "Room air distribution," ASHRAE Handbook, HVAC Applications, 2023, ch. 58, Table 5. [Online]. Available: https://handbook.ashrae.org/Handbooks/A23/IP/A23_Ch58/a23_ch58_ip.aspx']:
    p(text+' Accessed: Nov. 17, 2026.',small)
def footer(c,doc):c.setFont('Body',9);c.drawCentredString(A4[0]/2,30,str(doc.page))
out=R/'ADPI Design Assessment.pdf';SimpleDocTemplate(str(out),pagesize=A4,leftMargin=60,rightMargin=60,topMargin=45,bottomMargin=48).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
