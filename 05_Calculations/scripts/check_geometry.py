"""Plan-space obstacle and overlapping rigid-duct check, independent of sizing."""
import csv,json,sys
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon,LineString,box
from shapely.ops import polygonize,unary_union
R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data';rev=sys.argv[1] if len(sys.argv)>1 else 'v03'
def read(n):return list(csv.DictReader((D/f'{n}_{rev}.csv').open()))
source=ezdxf.readfile(R/'05_Calculations/.cache/source.dxf');O=(64345.93225182503,15925.58365525945)
cols=[]
for e in source.modelspace().query('LWPOLYLINE'):
    if e.dxf.layer=='ARCH' and len(e)==4:
        p=Polygon([(float(x)-O[0],float(y)-O[1]) for x,y in e.get_points('xy')])
        if abs(p.area-1125**2)<1 or abs(p.area-1125*1600)<1:cols.append(p)
lines=[LineString([(e.dxf.start.x-O[0],e.dxf.start.y-O[1]),(e.dxf.end.x-O[0],e.dxf.end.y-O[1])]) for e in source.modelspace().query('LINE') if e.dxf.layer=='ARCH']
cols.extend(p for p in polygonize(unary_union(lines)) if abs(p.area-1125**2)<1)
obstacles=unary_union(cols);clashes=[];shapes=[]
for r in read('diffusers'):
    x,y=float(r['x_mm']),float(r['y_mm']);shapes.append((r['id'],box(x-300,y-300,x+300,y+300)))
for r in read('vav_boxes'):
    x,y=float(r['x_mm']),float(r['y_mm']);shapes.append((r['id'],box(x-500,y-400,x+500,y+400)))
def segment(r):return LineString([(float(r['start_x_mm']),float(r['start_y_mm'])),(float(r['end_x_mm']),float(r['end_y_mm']))])
duct=read('ducts');flex=read('flex_routes')
shapes.extend((r['id'],segment(r).buffer(float(r['width_mm'])/2,cap_style=2)) for r in duct)
shapes.extend((r['id'],segment(r).buffer(float(r['diameter_mm'])/2,cap_style=2)) for r in flex)
for name,shape in shapes:
    if shape.intersection(obstacles).area>1:clashes.append(name)
overlaps=[]
for i,a in enumerate(duct):
    for b in duct[i+1:]:
        length=segment(a).intersection(segment(b)).length
        if length>1:overlaps.append({'a':a['id'],'b':b['id'],'overlap_mm':length})
result={'revision':rev,'architectural_columns_identified':len(cols),'column_clashes':clashes,'rigid_centerline_overlaps':overlaps,
        'scope':'2D column footprints and duplicate collinear duct paths only; not a 3D clearance/fire/structure approval.'}
(D/f'geometry_checks_{rev}.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
