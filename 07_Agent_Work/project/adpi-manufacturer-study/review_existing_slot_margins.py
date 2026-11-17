"""Resolve planar-L ambiguity and quantify the existing separate 63-slot design."""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import shape,Point,LineString
from bsa.manufacturer_adpi import screen
from fluids.numerics import interp
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';S=P/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected'
R=P/'runs/adpi-existing-slot-margin-review';R.mkdir(exist_ok=False)
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allocation=load(S/'allocation.json');selection=load(S/'Selected Linear Slot Schedule.json');previous=load(S/'slot-count-event-sample-check.json')
curvefile=P/'runs/manufacturer-type4-native-curves/curves.json';curves=load(curvefile)
boundaryfile=P/'project/bse3227-column-row-candidate/office-boundary.geojson';boundary=shape(load(boundaryfile))
assert all(abs(a[0]-b[0])<=1e-7 or abs(a[1]-b[1])<=1e-7 for ring in [boundary.exterior,*boundary.interiors] for a,b in zip(ring.coords,list(ring.coords)[1:]))
selected={t['id']:t for t in selection['terminals']};checks=[];summary=[]
for t in allocation['terminals']:
    x,y=t['center_m'];half=.6096;events=[y-half,y+half]
    events.extend(v['center_m'][1]+sign*half for v in allocation['terminals'] for sign in [-1,1] if y-half<v['center_m'][1]+sign*half<y+half)
    events.extend(py for ring in [boundary.exterior,*boundary.interiors] for px,py in ring.coords if y-half<py<y+half)
    events=sorted(set(events));samples=sorted(set(events+[(lo+hi)/2 for lo,hi in zip(events,events[1:])]))
    table=previous['tables'][selected[t['id']]['selected']]['rows'];local=[]
    for sy in samples:
        for dx in [-1,1]:
            ray=boundary.intersection(LineString([(x,sy),(x+dx*200,sy)]));pieces=list(ray.geoms) if hasattr(ray,'geoms') else [ray]
            connected=[v for v in pieces if v.geom_type=='LineString' and v.distance(Point(x,sy))<1e-8];assert len(connected)==1
            L=max((vx-x)*dx for vx,vy in connected[0].coords)
            for other in allocation['terminals']:
                ox,oy=other['center_m'];along=(ox-x)*dx
                if other['id']!=t['id'] and along>1e-8 and abs(sy-oy)<=half+1e-10:L=min(L,along/2)
            for condition,loads in [('maximum',[40,60]),('minimum',[20,40])]:
                q=t[condition+'_flow_L_s']/1.2192;assert table[0]['flow_L_s_m']<=q<=table[-1]['flow_L_s_m']
                throw=interp(q,[r['flow_L_s_m'] for r in table],[r['T050_m'] for r in table])
                for load in loads:
                    value=screen(curves,load,throw/L)
                    row=dict(terminal=t['id'],selected=selected[t['id']]['selected'],sample_y_m=sy,direction='east' if dx==1 else 'west',condition=condition,load_Btuh_ft2=load,L_m=L,T050_m=throw,**value)
                    checks.append(row);local.append(row)
    assert all(r['status']=='paired_curve_threshold_met' for r in local)
    worst=min(local,key=lambda r:r['stroke_margin_lower_ADPI'])
    summary.append(dict(terminal=t['id'],selected=selected[t['id']]['selected'],checks=len(local),minimum_source_curve_lower_ADPI=worst['stroke_margin_lower_ADPI'],critical=worst))
worst=min(checks,key=lambda r:r['stroke_margin_lower_ADPI'])
result=dict(scope='Existing separate63-slot1900 comparison; unchanged geometry/specs and full source event partition. No replacement of required1400 coursework; no measured or actual-load-interpolated ADPI.',
    inputs={str(p.relative_to(B)):sha(p) for p in [S/'allocation.json',S/'Selected Linear Slot Schedule.json',S/'slot-count-event-sample-check.json',curvefile,boundaryfile]},
    characteristic_length_method='Planar wall or opposing-slot midplane; NO added ceiling/occupied-zone distance. ASHRAE2023Applications chapter58Table5 ceiling-slot row; troffer addition not transferred.',
    terminal_count=len(summary),curve_checks=len(checks),all_source_domain_and_paired80_checks_pass=True,
    minimum_source_curve_lower_ADPI=worst['stroke_margin_lower_ADPI'],critical=worst,
    exact_2D_event_partition='Axis-aligned source boundary and vertical finite slots verified. Events include every boundary vertex and opposing segment endpoint; interval lengths are constant. Not continuous3D flow or occupied-zone performance.',
    source_load_pair_assumption='40/60Btuh-ft2 at maximum,20/40at minimum; both endpoint curves pass. This does not mathematically prove intermediate-load monotonicity.',
    ADPI_measured=False,actual_load_interpolation_verified=False,coursework_1400_replaced=False,formal_coursework_package_changed=False,
    remaining=['1900differs from required1400/51400series','Ordered48inch vs4ftactive correspondence is a coursework specification assumption','Inlet/plenum and installation remain outside terminal-performance check'])
for name,data in [('checks.json',checks),('terminal-summary.json',summary),('review.json',result)]: (R/name).write_text(json.dumps(data,indent=2))
print(json.dumps(result,indent=2))
