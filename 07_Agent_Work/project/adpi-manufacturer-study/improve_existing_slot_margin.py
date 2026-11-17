"""Finite maximin selection among the six source-verified Frame-B specifications."""
import json,math,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from shapely.geometry import shape,box
from fluids.numerics import interp
from bsa.manufacturer_adpi import screen
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';S=P/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected'
R=P/'runs/adpi-slot-margin-improved';R.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(S/'allocation.json');old=read(S/'Selected Linear Slot Schedule.json');oldby={t['id']:t for t in old['terminals']}
tables=read(S/'slot-count-event-sample-check.json')['tables'];curves=read(P/'runs/manufacturer-type4-native-curves/curves.json')
boundary=shape(read(P/'project/bse3227-column-row-candidate/office-boundary.geojson'))
widths={'0.5inch-8slots':11.5,'1.0inch-2slots':5,'0.75inch-6slots':10.5,'0.75inch-4slots':7.5,'0.5inch-6slots':9,'1.5inch-2slots':6}
checks=read(P/'runs/adpi-existing-slot-margin-review/checks.json');by=defaultdict(list)
for c in checks:by[c['terminal']].append(c)
selected=[];attempts=[];footprints=[]
for t in a['terminals']:
    x,y=t['center_m'];options=[]
    for key,width in widths.items():
        g=box(x-width*.0254/2,y-48.75*.0254/2,x+width*.0254/2,y+48.75*.0254/2)
        if not boundary.covers(g):continue
        table=tables[key]['rows'];values=[];eligible=True;cases={}
        for condition,loads in [('maximum',[40,60]),('minimum',[20,40])]:
            q=t[condition+'_flow_L_s']/1.2192
            if not table[0]['flow_L_s_m']<=q<=table[-1]['flow_L_s_m']:eligible=False;break
            throw=interp(q,[r['flow_L_s_m'] for r in table],[r['T050_m'] for r in table]);pressure=interp(q,[r['flow_L_s_m'] for r in table],[r['static_Pa'] for r in table])
            cases[condition]=dict(flow_L_s=t[condition+'_flow_L_s'],flow_L_s_per_m=q,T050_m=throw,diffuser_section_static_Pa=pressure)
            for previous in by[t['id']]:
                if previous['condition']!=condition:continue
                value=screen(curves,previous['load_Btuh_ft2'],throw/previous['L_m'])
                if value['status']!='paired_curve_threshold_met':eligible=False;break
                values.append(dict(sample_y_m=previous['sample_y_m'],direction=previous['direction'],condition=condition,load_Btuh_ft2=previous['load_Btuh_ft2'],L_m=previous['L_m'],T050_m=throw,**value))
            if not eligible:break
        if eligible:
            worst=min(values,key=lambda c:c['stroke_margin_lower_ADPI']);options.append(dict(selected=key,source_curve_lower_ADPI=worst['stroke_margin_lower_ADPI'],critical=worst,cases=cases,checks=values,outer_body_width_m=width*.0254))
    assert options,t['id'];best=max(options,key=lambda o:(o['source_curve_lower_ADPI'],-o['cases']['maximum']['diffuser_section_static_Pa']))
    assert any(v['selected']==oldby[t['id']]['selected'] for v in options)
    result={k:v for k,v in oldby[t['id']].items() if k not in ['selected','cases','outer_body_width_m']}
    result.update({k:v for k,v in best.items() if k!='checks'});table=tables[best['selected']]
    result.update(slot_width_inch=float(table['slot_width_inch']),slots=table['slots'],frame='B',overall_length_m=48.75*.0254,source_page=table['pdf_page'],before_selected=oldby[t['id']]['selected'])
    selected.append(result);attempts.append(dict(id=t['id'],options=options))
    w=best['outer_body_width_m'];footprints.append(box(x-w/2,y-48.75*.0254/2,x+w/2,y+48.75*.0254/2))
collisions=[(i,j) for i,g in enumerate(footprints) for j,h in enumerate(footprints[:i]) if g.intersects(h)];assert not collisions
critical=min(selected,key=lambda t:t['source_curve_lower_ADPI'])
summary=dict(scope='Separate manufacturer1900comparison only; finite source-specification maximin refinement, same63positions/service areas/flows. Not a substitute for required1400coursework or actual-load ADPI certification.',
    terminals=63,source_verified_frame_spec_options=6,changed_specifications=sum(t['selected']!=t['before_selected'] for t in selected),
    source_curve_lower_ADPI_before=read(P/'runs/adpi-existing-slot-margin-review/review.json')['minimum_source_curve_lower_ADPI'],source_curve_lower_ADPI_after=critical['source_curve_lower_ADPI'],
    selected_specifications=dict(Counter(t['selected'] for t in selected)),critical=critical,
    all_paired_curve_checks_pass=True,all_footprints_inside=True,footprint_intersections=0,flows_and_positions_preserved=True,
    no_downward_distance_added=True,ADPI_measured=False,actual_load_interpolation_verified=False,formal_coursework_1400_replaced=False,native_drawing_status='pending specification update')
(R/'selection.json').write_text(json.dumps(dict(terminals=selected),indent=2));(R/'attempts.json').write_text(json.dumps(attempts,indent=2));(R/'review.json').write_text(json.dumps(summary,indent=2));(R/'allocation.json').write_bytes((S/'allocation.json').read_bytes())
print(json.dumps(summary,indent=2))
