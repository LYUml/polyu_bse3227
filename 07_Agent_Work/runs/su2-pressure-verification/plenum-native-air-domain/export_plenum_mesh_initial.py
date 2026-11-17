import json
import math
import sys
from pathlib import Path
import gmsh

p = Path(__file__).parent
family = int(sys.argv[1])
source = next(x for x in json.loads((p/'export-review.json').read_text())['representatives'] if x['family'] == family)
frame = source['source_record']['frame']
areas = {x['port_guid']: x for x in source['source_record']['candidate_port_areas']}
caps, outlets = [], []
for port in source['ports']:
    row = dict(port)
    row['origin_m'] = row.pop('point_m')
    row['outward_normal'] = row.pop('normal')
    row['clear_area_m2'] = row.pop('candidate_area_m2')
    if areas[row['guid']]['kind'] == 'rectangular_chamber_entry':
        row['marker'] = 'inlet'
        caps.append(row)
    else:
        local = [sum(frame[j][i]*(row['origin_m'][j]-frame[j][3]) for j in range(3)) for i in range(3)]
        outlets.append(((round(local[0], 10), math.copysign(1, local[1])), row))
for i, (_, row) in enumerate(sorted(outlets, key=lambda x: x[0])):
    row['marker'] = f'outlet_{i}'
    row['radius_m'] = math.sqrt(row['clear_area_m2']/math.pi)
    caps.append(row)
out = p/f'family-{family}-layers'
gmsh.initialize()
gmsh.option.setNumber('General.Terminal', 0)
try:
    gmsh.open(str(out/'air.msh'))
    volumes = gmsh.model.getEntities(3)
    surfaces = gmsh.model.getBoundary(volumes, combined=True, oriented=False)
    buckets = {row['marker']: [] for row in caps}
    walls = []
    for _, tag in surfaces:
        _, coordinates, _ = gmsh.model.mesh.getNodes(2, tag, includeBoundary=True)
        points = [coordinates[i:i+3] for i in range(0, len(coordinates), 3)]
        hits = []
        for row in caps:
            if points and max(abs(sum((a-b)*n for a, b, n in zip(point, row['origin_m'], row['outward_normal']))) for point in points) < 1e-8:
                if 'radius_m' not in row or max(math.dist(point, row['origin_m']) for point in points) <= row['radius_m']+1e-7:
                    hits.append(row)
        assert len(hits) <= 1
        if hits:
            buckets[hits[0]['marker']].append(tag)
        else:
            walls.append(tag)
    ids, coordinates, _ = gmsh.model.mesh.getNodes()
    xyz = {int(tag): coordinates[i*3:i*3+3] for i, tag in enumerate(ids)}
    reversed_surfaces = []
    for row in caps:
        tags = buckets[row['marker']]
        assert tags
        for tag in tags:
            signs = []
            types, _, arrays = gmsh.model.mesh.getElements(2, tag)
            for kind, nodes in zip(types, arrays):
                count = gmsh.model.mesh.getElementProperties(kind)[3]
                assert count in (3, 4)
                for i in range(0, len(nodes), count):
                    a, b, c = [xyz[int(t)] for t in nodes[i:i+3]]
                    u, v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
                    cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
                    signs.append(sum(x*y for x, y in zip(cross, row['outward_normal'])))
            assert signs
            if all(x < 0 for x in signs):
                gmsh.model.mesh.reverse([(2, tag)])
                reversed_surfaces.append(tag)
            else:
                assert all(x > 0 for x in signs), ('mixed cap orientation', tag)
        gmsh.model.addPhysicalGroup(2, tags, name=row['marker'])
    assert walls
    gmsh.model.addPhysicalGroup(2, walls, name='wall')
    gmsh.model.addPhysicalGroup(3, [tag for _, tag in volumes], name='fluid')
    gmsh.write(str(out/'air.su2'))
    (out/'boundary-source.json').write_text(json.dumps(dict(caps=caps, cap_surfaces=buckets, wall_surfaces=walls,
        reversed_cap_surfaces=reversed_surfaces, engineering_accepted=False), indent=2))
    print('Exported', family, 'cap surfaces', {k: len(v) for k, v in buckets.items()}, 'reversed', reversed_surfaces)
finally:
    gmsh.finalize()
