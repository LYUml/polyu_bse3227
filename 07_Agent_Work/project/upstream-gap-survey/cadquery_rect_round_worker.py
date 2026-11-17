"""Thin CadQuery2.6.1 loft/Boolean worker, no custom geometry kernel."""
import hashlib,json,sys
from pathlib import Path
import cadquery as cq
import importlib.metadata as metadata

source=Path(sys.argv[1]);out=Path(sys.argv[2]);assert not out.exists();out.mkdir()
assert metadata.version('cadquery')=='2.6.1'
assert metadata.version('cadquery-ocp')=='7.8.1.1.post1'
spec=json.loads(source.read_text());results=[]
for row in spec['cases']:
    w,h,d,t,L,a,b=[row[k] for k in ['width_m','height_m','diameter_m','section_offset_m','taper_length_m','start_length_m','end_length_m']]
    assert all(isinstance(x,(int,float)) and x>0 for x in [w,h,d,t,L,a,b])
    assert 2*t<min(w,h,d)
    def solid(offset,extension):
        ww,hh,rr=w+2*offset,h+2*offset,d/2+offset
        loft=cq.Workplane('XY').rect(ww,hh).workplane(offset=L).circle(rr).loft(ruled=True)
        entry=cq.Workplane('XY',origin=(0,0,-a-extension)).rect(ww,hh).extrude(a+extension)
        exit=cq.Workplane('XY',origin=(0,0,L)).circle(rr).extrude(b+extension)
        return loft.union(entry).union(exit)
    outer=solid(t,0);inner=solid(0,.0001)
    for kind,value in [('outer',outer),('inner',inner)]:
        assert value.val().isValid()
        assert value.val().exportBrep(str(out/(row['id']+'-'+kind+'.brep')))
    wall=outer.cut(inner).val()
    assert wall.isValid() and len(wall.Solids())==1 and wall.Volume()>0
    target=out/(row['id']+'.brep');assert wall.exportBrep(str(target))
    # CAD kernel coordinates are metres; default STEP exporter declares mm.
    # Scale exported STEP coordinates1000x so an SI-aware reader sees metres.
    cq.exporters.export(wall.scale(1000),str(out/(row['id']+'.step')))
    results.append(dict(id=row['id'],solid_valid=True,solid_count=1,volume_m3=wall.Volume(),
        brep_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        bounds_m=[wall.BoundingBox().xmin,wall.BoundingBox().ymin,wall.BoundingBox().zmin,
                  wall.BoundingBox().xmax,wall.BoundingBox().ymax,wall.BoundingBox().zmax]))
(out/'kernel-review.json').write_text(json.dumps(dict(cadquery=metadata.version('cadquery'),
    ocp=metadata.version('cadquery-ocp'),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),results=results,
    brep_coordinate_unit='m',step_coordinate_unit='mm',
    scope='Ruled loft with section-plane-offset walls; not constant surface-normal sheet thickness or product/fabrication acceptance'),indent=2))
print(json.dumps(dict(cases=len(results),valid=True)))
