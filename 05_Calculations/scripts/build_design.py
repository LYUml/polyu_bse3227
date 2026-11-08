"""One source for preliminary HVAC coordinates, air balance and duct sizing.
Inputs are explicit assumptions, not measured building equipment ratings.
"""
from pathlib import Path
import csv,json,math
from friction import select

R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data'
def save_csv(name,rows):
    with (D/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

basis={'revision':'v01 - design review', 'area_m2':1022.0,'total_load_W_m2':120.0,
       'room_sensible_heat_ratio':0.75,'room_temperature_C':24.0,'supply_temperature_C':12.0,
       'air_density_kg_m3':1.2,'air_cp_J_kgK':1006.0,'min_flow_fraction':0.4,
       'ceiling_height_m':2.7,'flex_connection_allowance_m':0.5,'flex_length_limit_m':4.0,
       'main_velocity_limit_ms':5.0,'branch_velocity_limit_ms':4.5,'friction_limit_Pa_m':0.8,
       'ADPI_course_screen_range':[1.0,3.4],
       'ADPI_status':'PROVISIONAL: ASHRAE 2015 louvered-face screening; manufacturer identifies 1400 as Type 3 circular pattern. Resolve classification before claiming verified ADPI compliance.',
       'load_status':'120 W/m2 total and SHR 0.75 are explicit preliminary design assumptions; not supplied by lecturer or prescribed by Hong Kong regulation.'}
basis['total_load_kW']=basis['area_m2']*basis['total_load_W_m2']/1000
basis['sensible_load_kW']=basis['total_load_kW']*basis['room_sensible_heat_ratio']
basis['supply_lps']=basis['sensible_load_kW']*1e6/(1.2*1006*12)
basis['minimum_supply_lps']=basis['supply_lps']*.4

# Local coordinates from the southwest outside corner of the supplied DWG, mm.
O=[64345.93225182503,15925.58365525945]
lower=(180.,180.,44820.,20670.)
upper=(30863.33,20670.,44820.,29800.)
xs=[2880,8280,14280,19680,25080,30480,36480,41880]
ys=[2970,7770,13170,17970]
ux=[32880,36480,40080,43080];uy=[23970,28170]
rows=[]
def populate(xvals,yvals,bounds,offset):
    xmin,ymin,xmax,ymax=bounds
    for j,y in enumerate(yvals):
        for i,x in enumerate(xvals):
            xl=xmin if i==0 else (xvals[i-1]+x)/2
            xr=xmax if i==len(xvals)-1 else (xvals[i+1]+x)/2
            yb=ymin if j==0 else (yvals[j-1]+y)/2
            yt=ymax if j==len(yvals)-1 else (yvals[j+1]+y)/2
            idx=len(rows)+1
            vi=offset+(j//2)*(len(xvals)//2)+i//2+1
            rows.append(dict(id=f'SD-{idx:02}',vav=f'VAV-{vi:02}',x_mm=x,y_mm=y,
                world_x_mm=x+O[0],world_y_mm=y+O[1],cell_xmin=xl,cell_ymin=yb,cell_xmax=xr,cell_ymax=yt,
                geometric_cell_m2=(xr-xl)*(yt-yb)/1e6,
                L_w_m=(x-xl)/1000,L_e_m=(xr-x)/1000,L_s_m=(y-yb)/1000,L_n_m=(yt-y)/1000,
                diffuser_type='600 panel / 8in neck' if offset==0 else '300 panel / 6in neck'))
populate(xs,ys,lower,0);populate(ux,uy,upper,8)
# Remove the artificial horizontal zone boundary at the open L-shaped junction.
# For the lower/upper interface use the midplane of the adjacent row, rather than
# claiming a wall exists. Directional L is a screening model for irregular cells.
for r in rows:
    if r['y_mm']==ys[-1] and r['x_mm']>upper[0]:r['L_n_m']=(uy[0]-ys[-1])/2000
    if r['y_mm']==uy[0]:r['L_s_m']=(uy[0]-ys[-1])/2000

perf={
 '600 panel / 8in neck':[(33,1.5,0.8,0),(66,2.9,3.2,0),(99,3.6,7.2,11),(132,4.2,12.8,20),(165,4.6,19.9,27),(198,5.1,28.7,32),(231,5.5,39.1,37),(264,5.9,51,41)],
 '300 panel / 6in neck':[(19,1.3,1.6,0),(37,2.5,6.4,0),(56,3.1,14.5,14),(65,3.3,19.7,21),(74,3.5,25.7,26),(93,4.0,40.2,35),(111,4.3,57.9,42),(120,4.5,67.9,45),(130,4.7,78.7,48)]}
def interp(kind,q,col):
    a=perf[kind]
    assert a[0][0]<=q<=a[-1][0],(kind,q,'No extrapolation permitted')
    for lo,hi in zip(a,a[1:]):
        if lo[0]<=q<=hi[0]:return lo[col]+(hi[col]-lo[col])*(q-lo[0])/(hi[0]-lo[0])
geo=sum(r['geometric_cell_m2'] for r in rows)
for r in rows:
    r['load_area_m2']=r['geometric_cell_m2']/geo*1022
    r['max_lps']=basis['supply_lps']*r['load_area_m2']/1022
    r['min_lps']=.4*r['max_lps']
    for mode in ['max','min']:
        r[mode+'_T025_m']=interp(r['diffuser_type'],r[mode+'_lps'],1)
        ratios=[r[mode+'_T025_m']/r['L_'+dir+'_m'] for dir in ['w','e','s','n']]
        r[mode+'_ratio_min']=min(ratios);r[mode+'_ratio_max']=max(ratios)
        r[mode+'_course_screen']=min(ratios)>=1 and max(ratios)<=3.4
    r['max_catalog_Ps_Pa']=interp(r['diffuser_type'],r['max_lps'],2)
    r['max_catalog_NC_est']=interp(r['diffuser_type'],r['max_lps'],3)

boxes=[];flex=[]
for k in range(1,11):
    bid=f'VAV-{k:02}';group=[r for r in rows if r['vav']==bid]
    x=sum(r['x_mm'] for r in group)/4;y=sum(r['y_mm'] for r in group)/4
    boxes.append(dict(id=bid,x_mm=x,y_mm=y,outlets=4,max_lps=sum(r['max_lps'] for r in group),min_lps=sum(r['min_lps'] for r in group),
        envelope_width_mm=1000,envelope_height_mm=800,envelope_basis='Schematic design allowance, not selected product dimensions'))
    for r in group:
        px=x+math.copysign(500,r['x_mm']-x);py=y+math.copysign(400,r['y_mm']-y)
        plan=math.hypot(r['x_mm']-px,r['y_mm']-py)/1000
        flex.append(dict(id='F-'+r['id'][3:],vav=bid,diffuser=r['id'],start_x_mm=px,start_y_mm=py,
            end_x_mm=r['x_mm'],end_y_mm=r['y_mm'],plan_length_m=plan,
            allowance_m=.5,design_length_m=plan+.5,limit_m=4,pass_length=plan+.5<=4,
            diameter_mm=250 if k<=8 else 200,max_lps=r['max_lps']))

# Rigid single-line tree. Corridor crossing is enclosed provisionally;
# boundary protection and headroom must be coordinated, not assumed existing.
segments=[]
def seg(id,a,b,boxids,kind='branch'):
    q=sum(v['max_lps'] for v in boxes if v['id'] in boxids)
    segments.append(dict(id=id,start_x_mm=a[0],start_y_mm=a[1],end_x_mm=b[0],end_y_mm=b[1],
        downstream_vavs=';'.join(boxids),flow_lps=q,length_m=math.dist(a,b)/1000,
        **select(q,5.0 if kind=='main' else 4.5),kind=kind))
allids=[v['id'] for v in boxes]
seg('M01',(19200,24600),(19200,19500),allids,'main')
left=[f'VAV-{k:02}' for k in [1,2,5,6]];right=[x for x in allids if x not in left]
seg('M02',(19200,19500),(16980,19500),left,'main')
seg('M03',(16980,19500),(5580,19500),['VAV-01','VAV-05'],'main')
seg('M04',(19200,19500),(27780,19500),right,'main')
seg('M05',(27780,19500),(39180,19500),['VAV-04','VAV-08','VAV-09','VAV-10'],'main')
for c,x in enumerate([5580,16980,27780,39180],1):
    low=boxes[c-1];high=boxes[c+3]
    seg(f'B{c:02}A',(x,19500),(x,high['y_mm']+400),[low['id'],high['id']])
    # Take off to the high box; bypass on a rigid offset so it does not run through the box.
    seg(f'B{c:02}B',(x,high['y_mm']+400),(x-900,high['y_mm']+400),[low['id']])
    seg(f'B{c:02}C',(x-900,high['y_mm']+400),(x-900,low['y_mm']+1400),[low['id']])
    seg(f'B{c:02}D',(x-900,low['y_mm']+1400),(x,low['y_mm']+1400),[low['id']])
    seg(f'B{c:02}E',(x,low['y_mm']+1400),(x,low['y_mm']+400),[low['id']])
seg('M06',(39180,19500),(39180,24700),['VAV-09','VAV-10'],'main')
for i in [9,10]:
    v=boxes[i-1];seg(f'B{i:02}A',(39180,24700),(v['x_mm'],24700),[v['id']])
    seg(f'B{i:02}B',(v['x_mm'],24700),(v['x_mm'],v['y_mm']-400),[v['id']])

save_csv('diffusers_v01.csv',rows);save_csv('vav_boxes_v01.csv',boxes);save_csv('flex_routes_v01.csv',flex);save_csv('ducts_v01.csv',segments)
(D/'design_basis_v01.json').write_text(json.dumps(basis,indent=2))
(D/'diffuser_performance_rows.json').write_text(json.dumps({'source':'Krueger 2012 B1-11/12; metric data; no damper; third throw is T0.25; NC=0 denotes catalog dash (<10), not measured zero','columns':['lps','T025_m','Ps_Pa','NC'], 'data':perf},indent=2))
checks={'diffusers':len(rows),'vav_boxes':len(boxes),'outlets_per_box':4,'rigid_sections':len(segments),
        'flow_lps':sum(r['max_lps'] for r in rows),'geometric_envelope_m2':geo,'load_area_m2':1022,
        'geometry_area_note':'Envelope cells include small columns and edge recesses; 1022 m2 printed area used for loads, prorated across cells. No claim that envelope equals net office area.',
        'max_flex_m':max(f['design_length_m'] for f in flex),'flex_pass':all(f['pass_length'] for f in flex),
        'course_ADPI_failures':[r['id'] for r in rows if not(r['max_course_screen'] and r['min_course_screen'])],
        'manufacturer_classification_resolved':False,'release_status':'PRELIMINARY / NOT ACCEPTED'}
(D/'design_checks_v01.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
