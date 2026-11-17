from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import numpy as np

p = Path(__file__).parent/f'family-{int(sys.argv[1])}-layers'
mesh = p/(sys.argv[2] if len(sys.argv) > 2 else 'air.su2')
patterns = {10: ((0,1,2),(0,1,3),(0,2,3),(1,2,3)),
            13: ((0,1,2),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))}
with mesh.open() as stream:
    assert stream.readline().strip().replace(' ', '') == 'NDIME=3'
    ne = int(stream.readline().split('=')[1])
    for _ in range(ne):
        stream.readline()
    nn = int(stream.readline().split('=')[1])
    xyz = np.array([list(map(float, stream.readline().split()[:3])) for _ in range(nn)])
    nm = int(stream.readline().split('=')[1])
    markers, boundary = {}, Counter()
    for _ in range(nm):
        name = stream.readline().split('=')[1].strip()
        count = int(stream.readline().split('=')[1])
        assert name not in markers
        markers[name] = []
        for _ in range(count):
            row = list(map(int, stream.readline().split()))
            assert row[0] in (5,9)
            face = row[1:4] if row[0] == 5 else row[1:5]
            markers[name].append(face)
            boundary[tuple(sorted(face))] += 1
assert max(boundary.values()) == 1
faces, owner_centers = Counter(), {}
with mesh.open() as stream:
    stream.readline()
    stream.readline()
    for _ in range(ne):
        row = list(map(int, stream.readline().split()))
        cell = row[1:5] if row[0] == 10 else row[1:7]
        assert row[0] in patterns
        for indices in patterns[row[0]]:
            key = tuple(sorted(cell[i] for i in indices))
            faces[key] += 1
            if key in boundary:
                assert key not in owner_centers
                owner_centers[key] = xyz[cell].mean(axis=0)
assert max(faces.values()) == 2
exterior = {face for face, count in faces.items() if count == 1}
assert exterior == set(boundary) == set(owner_centers)
inward = {}
for name, entries in markers.items():
    bad = 0
    for face in entries:
        coords = xyz[face]
        normal = np.cross(coords[1]-coords[0], coords[2]-coords[0])
        bad += np.dot(normal, coords.mean(axis=0)-owner_centers[tuple(sorted(face))]) <= 0
    inward[name] = int(bad)
walls = {i for face in markers['wall'] for i in face}
caps = []
for source in json.loads((p/'boundary-source.json').read_text())['caps']:
    area, effective, bad, maximum_plane_error = 0., 0., 0, 0.
    for face in markers[source['marker']]:
        coords = xyz[face]
        maximum_plane_error = max(maximum_plane_error, float(np.max(np.abs((coords-source['origin_m'])@source['outward_normal']))))
        center = coords.mean(axis=0)
        for i, node in enumerate(face):
            point = coords[i]
            previous = (point+coords[i-1])/2
            following = (point+coords[(i+1)%len(face)])/2
            patch = (np.linalg.norm(np.cross(previous-point, center-point))+
                     np.linalg.norm(np.cross(center-point, following-point)))/2
            area += patch
            effective += patch*(node not in walls)
        for ids in ([face] if len(face) == 3 else [[face[0],face[1],face[2]],[face[0],face[2],face[3]]]):
            coords = xyz[ids]
            normal = np.cross(coords[1]-coords[0], coords[2]-coords[0])
            bad += np.dot(normal, source['outward_normal']) <= 0
    assert maximum_plane_error < 1e-8 and bad == 0
    relative = abs(area/source['clear_area_m2']-1)
    assert relative < .001
    caps.append(dict(marker=source['marker'], area_m2=float(area), relative_area_error=relative,
                     zero_wall_edge_effective_area_m2=float(effective), maximum_plane_error_m=maximum_plane_error))
report = dict(nodes=nn, elements=ne, closed_exterior_face_incidence=True,
              boundary_inward_faces=inward, caps=caps,
              mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(), engineering_accepted=False)
(p/'export-topology-review.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
assert not any(inward.values()), 'Boundary orientation requires correction'
