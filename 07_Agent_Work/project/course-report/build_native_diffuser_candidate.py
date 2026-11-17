"""Project-only bounded revision using existing native export/plot and preservation."""
import json,math,shutil,hashlib
from pathlib import Path
import ezdxf
from shapely.geometry import shape,LineString,Polygon
from bsa.native_cad import execute,lisp_string,DEFAULT_EXE
from bsa.cad_intake import export_dwg
from bsa.cad_sheet import plot
from bsa.drawing_revision import snapshot

B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
R=B/'07_Agent_Work/runs/course-diffuser-native-final';R.mkdir(exist_ok=False)
source=B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.dwg'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(source)
copy=R/'Supply Air Distribution.dwg';shutil.copy2(source,copy)
before_path=export_dwg(source,R/'source',DEFAULT_EXE)
d=ezdxf.readfile(before_path)
candidate=json.loads((B/'07_Agent_Work/runs/course-diffuser-fixed-service-checked/review.json').read_text())
allocation=json.loads((B/'07_Agent_Work/runs/vav-recenter-design-reviewed/delivery/allocation/allocation.json').read_text())
old={t['id']:t['center_m'] for t in allocation['terminals']}
space=shape(json.loads((B/'07_Agent_Work/project/bse3227-column-row-candidate/office-boundary.geojson').read_text()))
commands=[];edits=[];touched=set()
near=lambda a,b:math.dist(a,b)<1e-5
for ident,xy in candidate['changes'].items():
    previous=old[ident];delta=[(xy[i]-previous[i])*1000 for i in range(2)]
    symbols=[e for e in d.modelspace().query('LWPOLYLINE') if e.dxf.layer=='BSA_DIFFUSER' and near([sum(p[i] for p in e.get_points())/4/1000 for i in range(2)],previous)]
    labels=[e for e in d.modelspace().query('TEXT') if e.dxf.layer=='BSA_LABEL' and e.dxf.text==ident]
    lines=[e for e in d.modelspace().query('LINE') if e.dxf.layer=='BSA_FLEX' and any(near([p.x/1000,p.y/1000],previous) for p in [e.dxf.start,e.dxf.end])]
    assert len(symbols)==len(labels)==len(lines)==1
    symbol,label,line=symbols[0],labels[0],lines[0]
    assert not touched.intersection(e.dxf.handle for e in [symbol,label,line])
    for e in [symbol,label]:
        commands.append(f'(command "_.MOVE" (handent "{e.dxf.handle}") "" "0,0,0" "{delta[0]:.9f},{delta[1]:.9f},0")')
    symbol.set_points([(p[0]+delta[0],p[1]+delta[1],*p[2:]) for p in symbol.get_points()]);label.translate(*delta,0)
    panel=Polygon([(p[0]/1000,p[1]/1000) for p in symbol.get_points()]);assert space.covers(panel)
    attr='start' if near([line.dxf.start.x/1000,line.dxf.start.y/1000],previous) else 'end'
    p=getattr(line.dxf,attr);setattr(line.dxf,attr,[xy[0]*1000,xy[1]*1000,p.z])
    code=10 if attr=='start' else 11
    commands.append(f'(setq en (handent "{line.dxf.handle}") ed (entget en)) (entmod (subst (cons {code} (list {xy[0]*1000:.9f} {xy[1]*1000:.9f} 0.0)) (assoc {code} ed) ed)) (entupd en)')
    segment=LineString([[line.dxf.start.x/1000,line.dxf.start.y/1000],[line.dxf.end.x/1000,line.dxf.end.y/1000]])
    assert space.buffer(1e-7).covers(segment),'New flex outside interpreted office/column boundary'
    touched.update(e.dxf.handle for e in [symbol,label,line]);edits.append(dict(terminal=ident,handles=[e.dxf.handle for e in [symbol,label,line]],delta_mm=delta))
lengths=[math.dist(e.dxf.start,e.dxf.end)/1000 for e in d.modelspace().query('LINE') if e.dxf.layer=='BSA_FLEX'];assert len(lengths)==80 and max(lengths)+.5<4
expected=snapshot(d)
condition=f'(= (strcase (vl-string-translate (chr 92) "/" (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))) (strcase {lisp_string(copy)}))'
script=R/'revise.scr';script.write_text('\n'.join(f'(if {condition} (progn {command}) (princ "BSA WRONG DOCUMENT"))' for command in [*commands,'(command "_.QSAVE")'])+'\n_.QUIT\n_Y\n',encoding='ascii')
execute(DEFAULT_EXE,copy,script,R/'revision.log',120)
reopened=export_dwg(copy,R/'reopened',DEFAULT_EXE);actual=snapshot(ezdxf.readfile(reopened))
def equal(a,b):
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,abs_tol=1e-7,rel_tol=0)
    return a==b
differences=[k for k in expected.keys()|actual.keys() if not equal(expected.get(k),actual.get(k))]
assert not differences,differences[:10]
sheet=json.loads((B/'07_Agent_Work/project/bse3227-flow-direction-inputs/native.json').read_text())['sheet']
plotted=plot(copy,reopened,sheet,R/'Supply Air Distribution.pdf',DEFAULT_EXE)
assert sha(source)==source_sha
record=dict(source_sha256=source_sha,candidate_dwg_sha256=sha(copy),plot=plotted,native_reopen_pass=True,preserved_records=len(expected),
    changed_handles=len(touched),edits=edits,maximum_plan_flex_m=max(lengths),total_plan_flex_m=sum(lengths),
    assumed_routing_allowance_m=.5,maximum_conditional_flex_m=max(lengths)+.5,
    all80_flex_and12_panel_obstruction_checks=True,rigid_ducts_and_flows_unchanged=True,source_unchanged=True,
    visual_review='pending',selected=False,ADPI_verified=False,design_accepted=False)
(R/'review.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:v for k,v in record.items() if k!='edits'},indent=2))
