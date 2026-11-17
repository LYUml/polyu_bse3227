"""Source-coordinate vector figures; no simulated air-speed/temperature fields."""
from reportlab.graphics.shapes import Drawing,Path,Line,Rect,Circle,String,Polygon
from reportlab.lib import colors
import json
from pathlib import Path as FilePath

B=FilePath('C:/Users/lyuml-win/Desktop/polyu_bse3227')
blue=colors.HexColor('#206887');orange=colors.HexColor('#B55024')

def outline(d,geometry,transform,stroke=colors.grey,fill=None,width=.5):
    polys=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
    for polygon in polys:
        for ring in polygon:
            p=Path(strokeColor=stroke,fillColor=fill,strokeWidth=width)
            for i,xy in enumerate(ring):
                x,y=transform(xy)
                (p.moveTo if i==0 else p.lineTo)(x,y)
            p.closePath();d.add(p)

def overview(width,allocation,groups,vav_centres,changes):
    d=Drawing(width,290);boundary=json.loads((B/'07_Agent_Work/project/bse3227-column-row-candidate/office-boundary.geojson').read_text())
    coords=[xy for polygon in ([boundary['coordinates']] if boundary['type']=='Polygon' else boundary['coordinates']) for ring in polygon for xy in ring]
    xmin=min(p[0] for p in coords);ymin=min(p[1] for p in coords);xmax=max(p[0] for p in coords);ymax=max(p[1] for p in coords)
    scale=min((width-24)/(xmax-xmin),245/(ymax-ymin));tr=lambda p:(12+(p[0]-xmin)*scale,30+(p[1]-ymin)*scale)
    outline(d,boundary,tr,stroke=colors.black,width=.9)
    terms={t['id']:t for t in allocation['terminals']}
    for g in groups:
        centre=vav_centres[g['VAV']];x,y=tr(centre)
        for tid in g['Diffuser outlets'].split(', '):
            tx,ty=tr(terms[tid]['center_m']);d.add(Line(x,y,tx,ty,strokeColor=colors.HexColor('#AABAC2'),strokeWidth=.45))
        d.add(Circle(x,y,2.2,fillColor=blue,strokeColor=blue));d.add(String(x+3,y+2,g['VAV'].replace('VAV-','V'),fontName='Body',fontSize=6.5,fillColor=blue))
    for tid,t in terms.items():
        x,y=tr(t['center_m']);c=orange if tid in changes else colors.black
        d.add(Rect(x-.3*scale,y-.3*scale,.6*scale,.6*scale,strokeColor=c,fillColor=None,strokeWidth=.8))
    for tid,offset in [('SD-56',(8,-17)),('SD-08',(8,-17))]:
        x,y=tr(terms[tid]['center_m']);lx,ly=x+offset[0],y+offset[1]
        d.add(Line(x+2,y-2,lx,ly+3,strokeColor=orange,strokeWidth=.6))
        d.add(Rect(lx-1,ly-2,27,10,fillColor=colors.white,strokeColor=None))
        d.add(String(lx,ly,tid,fontName='Bold',fontSize=8,fillColor=orange))
    d.add(String(12,14,'Square: diffuser   Blue dot: schematic VAV   Orange: 150 mm southward adjustment',fontName='Body',fontSize=8))
    d.add(String(12,2,'Source plan coordinates; existing service areas, flows and group membership retained.',fontName='Body',fontSize=8))
    return d

def critical_detail(width,allocation,geometry_case,critical):
    d=Drawing(width,245);terms={t['id']:t for t in allocation['terminals']};tid=critical['terminal'];xy=terms[tid]['center_m']
    peer=geometry_case['aligned_midpoint_candidate']['terminal'];other=terms[peer]['center_m'];L=float(critical['L_m']);throw=float(critical['native_T025_m'])
    scale=36;cx=width*.37;cy=48;tr=lambda p:(cx+(p[0]-xy[0])*scale,cy+(p[1]-xy[1])*scale)
    for ident in [tid,peer]:
        x,y=tr(terms[ident]['center_m']);d.add(Rect(x-10.8,y-10.8,21.6,21.6,strokeColor=blue,fillColor=None,strokeWidth=1));d.add(String(x+18,y-3,ident,fontName='Bold',fontSize=10))
    mid=cy+L*scale
    d.add(Line(30,mid,width-25,mid,strokeColor=colors.grey,strokeDashArray=[4,3]));d.add(String(width-145,mid+5,'Opposing-outlet midplane',fontName='Body',fontSize=9))
    d.add(Line(cx-42,cy,cx-42,mid,strokeColor=colors.black));
    for y in [cy,mid]:d.add(Line(cx-47,y,cx-37,y,strokeColor=colors.black))
    d.add(String(12,(cy+mid)/2,f'L = {L:.4f} m',fontName='Body',fontSize=10))
    end=cy+throw*scale;ax=cx-16;d.add(Line(ax,cy,ax,end,strokeColor=orange,strokeWidth=1.4,strokeDashArray=[4,2]));d.add(Polygon([ax,end,ax-3,end-7,ax+3,end-7],fillColor=orange,strokeColor=orange))
    d.add(String(cx+14,end,f'Native isothermal throw = {throw:.3f} m',fontName='Body',fontSize=9,fillColor=orange))
    d.add(String(12,18,'Plan schematic from actual coordinates. Dashed arrow denotes tabulated isothermal throw,',fontName='Body',fontSize=8))
    d.add(String(12,6,'not a simulated jet path or measured occupied-zone velocity. North is upwards.',fontName='Body',fontSize=8))
    return d
