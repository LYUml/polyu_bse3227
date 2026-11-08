"""Course-workshop revision; preserves superseded v01 data."""
from pathlib import Path
import csv,json,math
from friction import select
R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data'
def save(name,rows):
    with (D/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
course=json.loads((D/'course_workshop_basis.json').read_text())
b=dict(revision='v03 course workshop',area_m2=1022,total_load_W_m2=189,room_sensible_heat_ratio=.9,
       room_temperature_C=24,supply_temperature_C=12,air_density_kg_m3=1.2,air_cp_J_kgK=1006,
       min_flow_fraction=.4,ceiling_height_m=2.7,main_velocity_limit_ms=10,branch_velocity_limit_ms=8,
       friction_limit_Pa_m=.8,flex_length_limit_m=4,flex_connection_allowance_m=.5,
       course_ADPI_ratio_range=[1,3.4],source='course_workshop_basis.json',
       qualifications=course['ADPI_qualification'])
b['total_load_kW']=1022*189/1000;b['sensible_load_kW']=b['total_load_kW']*.9
b['supply_lps']=b['sensible_load_kW']*1e6/(1.2*1006*12);b['minimum_supply_lps']=b['supply_lps']*.4
O=[64345.93225182503,15925.58365525945]
xs=[2280,5880,9480,13080,16680,20280,24480,28080,31680,35280,38880,42480]
ys=[1770,5370,8970,11970,15570,19170]
# Equal upper-zone spacing avoids the short 1.5 m opposing-jet distance in v01.
# These eight outlets require local ceiling-grid coordination, explicitly noted.
ux=[30863.33+(i+.5)*(44820-30863.33)/4 for i in range(4)];uy=[23970,28170]
rows=[]
def populate(xx,yy,bd,offset):
    xmin,ymin,xmax,ymax=bd
    for j,y in enumerate(yy):
        for i,x in enumerate(xx):
            xl=xmin if i==0 else (xx[i-1]+x)/2;xr=xmax if i==len(xx)-1 else (xx[i+1]+x)/2
            yb=ymin if j==0 else (yy[j-1]+y)/2;yt=ymax if j==len(yy)-1 else (yy[j+1]+y)/2
            k=offset+(j//2)*(len(xx)//2)+i//2+1
            rows.append(dict(id=f'SD-{len(rows)+1:02}',vav=f'VAV-{k:02}',x_mm=x,y_mm=y,world_x_mm=x+O[0],world_y_mm=y+O[1],
              cell_xmin=xl,cell_ymin=yb,cell_xmax=xr,cell_ymax=yt,geometric_cell_m2=(xr-xl)*(yt-yb)/1e6,
              L_w_m=(x-xl)/1000,L_e_m=(xr-x)/1000,L_s_m=(y-yb)/1000,L_n_m=(yt-y)/1000,
              diffuser_type='600 panel / 8in neck'))
populate(xs,ys,(180,180,44820,20670),0)
populate(ux,uy,(30863.33,20670,44820,29800),18)
for r in rows:
    if r['y_mm']==ys[-1] and r['x_mm']>30863.33:r['L_n_m']=(uy[0]-ys[-1])/2000
    if r['y_mm']==uy[0]:r['L_s_m']=(uy[0]-ys[-1])/2000
perf=json.loads((D/'diffuser_performance_rows.json').read_text())['data']['600 panel / 8in neck']
def interp(q,col):
    assert perf[0][0]<=q<=perf[-1][0],('No extrapolation',q)
    for lo,hi in zip(perf,perf[1:]):
        if lo[0]<=q<=hi[0]:return lo[col]+(hi[col]-lo[col])*(q-lo[0])/(hi[0]-lo[0])
geo=sum(r['geometric_cell_m2'] for r in rows)
for r in rows:
    r['load_area_m2']=r['geometric_cell_m2']/geo*1022
    r['max_lps']=b['supply_lps']*r['load_area_m2']/1022;r['min_lps']=.4*r['max_lps']
    for mode in ['max','min']:
        r[mode+'_T025_m']=interp(r[mode+'_lps'],1)
        ratios=[r[mode+'_T025_m']/r[f'L_{d}_m'] for d in ['w','e','s','n']]
        r[mode+'_ratio_min']=min(ratios);r[mode+'_ratio_max']=max(ratios)
        r[mode+'_course_screen']=min(ratios)>=1 and max(ratios)<=3.4
    r['max_catalog_Ps_Pa']=interp(r['max_lps'],2);r['max_catalog_NC_est']=interp(r['max_lps'],3)
boxes=[];flex=[]
for k in range(1,21):
    bid=f'VAV-{k:02}';g=[r for r in rows if r['vav']==bid]
    x=sum(r['x_mm'] for r in g)/4;y=sum(r['y_mm'] for r in g)/4
    boxes.append(dict(id=bid,x_mm=x,y_mm=y,outlets=4,max_lps=sum(r['max_lps'] for r in g),min_lps=sum(r['min_lps'] for r in g),
       envelope_width_mm=1000,envelope_height_mm=800,envelope_basis='Schematic allowance, not selected product dimensions'))
    for r in g:
        px=x+math.copysign(500,r['x_mm']-x);py=y+math.copysign(400,r['y_mm']-y)
        plan=math.hypot(r['x_mm']-px,r['y_mm']-py)/1000
        flex.append(dict(id='F-'+r['id'][3:],vav=bid,diffuser=r['id'],start_x_mm=px,start_y_mm=py,end_x_mm=r['x_mm'],end_y_mm=r['y_mm'],
          plan_length_m=plan,allowance_m=.5,design_length_m=plan+.5,limit_m=4,pass_length=plan+.5<=4,diameter_mm=250,max_lps=r['max_lps']))
duct=[]
def seg(id,a,z,ids,kind='branch'):
    q=sum(v['max_lps'] for v in boxes if v['id'] in ids)
    duct.append(dict(id=id,start_x_mm=a[0],start_y_mm=a[1],end_x_mm=z[0],end_y_mm=z[1],downstream_vavs=';'.join(ids),flow_lps=q,length_m=math.dist(a,z)/1000,
      **select(q,10 if kind=='main' else 8,.8),kind=kind))
allids=[v['id'] for v in boxes]
seg('M01',(19200,24600),(19200,20000),allids,'main')
# Main trunk arms. Six vertical risers run beside, rather than through, VAVs.
cols=[boxes[c]['x_mm']-800 for c in range(6)]
def column_ids(c):return [boxes[c+6*j]['id'] for j in range(3)]
left=[c for c,x in enumerate(cols) if x<19200];right=[c for c,x in enumerate(cols) if x>19200]
last=19200;mi=2
for c in reversed(left):
    ids=sum((column_ids(k) for k in left if cols[k]<=cols[c]),[])
    seg(f'M{mi:02}',(last,20000),(cols[c],20000),ids,'main');last=cols[c];mi+=1
last=19200
for c in right:
    ids=sum((column_ids(k) for k in right if cols[k]>=cols[c]),[])+['VAV-19','VAV-20']
    seg(f'M{mi:02}',(last,20000),(cols[c],20000),ids,'main');last=cols[c];mi+=1
for c,x in enumerate(cols):
    last=20000
    for j in [2,1,0]:
        v=boxes[c+6*j];y=v['y_mm']+400
        ids=[boxes[c+6*k]['id'] for k in range(j+1)]
        seg(f'R{c+1}{j+1}',(x,last),(x,y),ids)
        seg(f'B{c+6*j+1:02}',(x,y),(v['x_mm'],y),[v['id']]);last=y
seg(f'M{mi:02}',(cols[-1],20000),(41600,20000),['VAV-19','VAV-20'],'main');mi+=1
seg(f'M{mi:02}',(41600,20000),(41600,24700),['VAV-19','VAV-20'],'main')
for v in boxes[18:]:
    k=v['id'][-2:];seg(f'B{k}A',(41600,24700),(v['x_mm'],24700),[v['id']]);seg(f'B{k}B',(v['x_mm'],24700),(v['x_mm'],v['y_mm']-400),[v['id']])
save('diffusers_v03.csv',rows);save('vav_boxes_v03.csv',boxes);save('flex_routes_v03.csv',flex);save('ducts_v03.csv',duct)
(D/'design_basis_v03.json').write_text(json.dumps(b,indent=2))
checks=dict(diffusers=len(rows),vav_boxes=len(boxes),rigid_sections=len(duct),max_flow_lps=sum(r['max_lps'] for r in rows),
 max_flex_m=max(f['design_length_m'] for f in flex),max_NC_est=max(r['max_catalog_NC_est'] for r in rows),
 course_ADPI_failures=[r['id'] for r in rows if not(r['max_course_screen'] and r['min_course_screen'])],
 source='course_workshop_basis.json',status='CALCULATION CANDIDATE - native geometry/plot verification outstanding',
 qualification=b['qualifications'])
(D/'design_checks_v03.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
