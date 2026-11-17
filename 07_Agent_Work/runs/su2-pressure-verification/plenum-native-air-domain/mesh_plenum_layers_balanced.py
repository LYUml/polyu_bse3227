import json
import math
import sys
from pathlib import Path
import gmsh

p = Path(__file__).parent
family = int(sys.argv[1])
source = next(x for x in json.loads((p/'export-review.json').read_text())['representatives'] if x['family'] == family)
out = p/f'family-{family}-layers-balanced'
out.mkdir(exist_ok=False)
gmsh.initialize()
gmsh.option.setNumber('General.Terminal', 1)
gmsh.option.setNumber('General.NumThreads', 4)
try:
    gmsh.model.add('plenum')
    volumes = gmsh.model.occ.importShapes(str(p/f'family-{family}-air.brep'))
    gmsh.model.occ.synchronize()
    surfaces = gmsh.model.getBoundary(volumes, oriented=False)
    caps = set()
    for port in source['ports']:
        matches = [tag for dim, tag in surfaces if dim == 2 and math.dist(gmsh.model.occ.getCenterOfMass(2, tag), port['point_m']) < 1e-7]
        assert len(matches) == 1
        caps.add(matches[0])
    walls = [(dim, tag) for dim, tag in surfaces if tag not in caps]
    gmsh.model.occ.remove(volumes, recursive=False)
    gmsh.model.occ.remove([(2, tag) for tag in caps], recursive=False)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', .04)
    gmsh.option.setNumber('Mesh.MeshSizeMin', .005)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 128)
    heights, height = [], 0
    for i in range(18):
        height += .00003*1.2959264707672928**i
        heights.append(-height)
    extruded = gmsh.model.geo.extrudeBoundaryLayer(walls, [1]*18, heights, True)
    gmsh.model.geo.synchronize()
    top = [extruded[i-1] for i in range(1, len(extruded)) if extruded[i][0] == 3]
    curves = gmsh.model.getBoundary(top, combined=True, oriented=False)
    ends = {tag: {x[1] for x in gmsh.model.getBoundary([(1, tag)], oriented=False)} for _, tag in curves}
    todo, groups = set(ends), []
    while todo:
        group = {todo.pop()}
        points = set(ends[next(iter(group))])
        while True:
            adjacent = {tag for tag in todo if points & ends[tag]}
            if not adjacent:
                break
            for tag in adjacent:
                points |= ends[tag]
            group |= adjacent
            todo -= adjacent
        groups.append(sorted(group))
    assert len(groups) == 5, ('port loops', len(groups))
    new_caps = [gmsh.model.geo.addPlaneSurface([gmsh.model.geo.addCurveLoop(group, reorient=True)]) for group in groups]
    loop = gmsh.model.geo.addSurfaceLoop([tag for _, tag in top]+new_caps)
    gmsh.model.geo.addVolume([loop])
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(3)
    gmsh.write(str(out/'air.msh'))
    types, element_tags, _ = gmsh.model.mesh.getElements(3)
    tags = [int(tag) for group in element_tags for tag in group]
    quality = gmsh.model.mesh.getElementQualities(tags, 'minSICN')
    volumes = gmsh.model.mesh.getElementQualities(tags, 'volume')
    assert min(quality) > 0 and min(volumes) > 0
    volume = sum(volumes)
    assert abs(volume/source['analytic_air_volume_m3']-1) < .001
    report = dict(family=family, nodes=len(gmsh.model.mesh.getNodes()[0]), cells=len(tags),
                  element_types=[int(x) for x in types], minimum_SICN=min(quality),
                  minimum_signed_volume_m3=min(volumes), volume_m3=volume,
                  port_loops=5, first_layer_m=.00003, layers=18, growth=1.2959264707672928, original_layer_total_m=0.010672796259849524,
                  scope='Numerical mesh only; boundary export, y-plus, pressure and physical acceptance pending.',
                  engineering_accepted=False)
    (out/'mesh-review.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
except Exception as exc:
    (out/'failure.json').write_text(json.dumps(dict(error=str(exc), engineering_accepted=False)))
    raise
finally:
    gmsh.finalize()
