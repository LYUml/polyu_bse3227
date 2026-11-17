from collections import Counter
from pathlib import Path
import hashlib
import json
import sys

p = Path(__file__).parent/f'family-{int(sys.argv[1])}-layers'
source = p/'air.su2'
lines = source.read_bytes().splitlines(keepends=True)
ne = int(lines[1].split(b'=')[1])
patterns = {10: ((0,1,2),(0,1,3),(0,2,3),(1,2,3)),
            13: ((0,1,2),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))}
faces = Counter()
for line in lines[2:2+ne]:
    row = list(map(int, line.split()))
    for indices in patterns[row[0]]:
        faces[tuple(sorted(row[i+1] for i in indices))] += 1
assert max(faces.values()) <= 2
cursor = 2+ne
nn = int(lines[cursor].split(b'=')[1])
cursor += 1+nn
nm = int(lines[cursor].split(b'=')[1])
prefix = b''.join(lines[:cursor+1])
output = [prefix]
cursor += 1
removed = Counter()
seen = set()
for _ in range(nm):
    tag_line = lines[cursor]
    name = tag_line.split(b'=')[1].strip().decode()
    count = int(lines[cursor+1].split(b'=')[1])
    cursor += 2
    kept = []
    for line in lines[cursor:cursor+count]:
        row = list(map(int, line.split()))
        assert row[0] in (5,9)
        key = tuple(sorted(row[1:4] if row[0] == 5 else row[1:5]))
        assert key not in seen
        seen.add(key)
        assert faces[key] in (1,2)
        if faces[key] == 2:
            assert name == 'wall', 'Do not silently discard an inlet or outlet'
            removed[name] += 1
        else:
            kept.append(line)
    cursor += count
    output += [tag_line, f'MARKER_ELEMS= {len(kept)}\n'.encode(), *kept]
assert {key for key, count in faces.items() if count == 1}.issubset(seen)
output += lines[cursor:]
data = b''.join(output)
assert data.startswith(prefix)
(p/'air-exterior.su2').write_bytes(data)
(p/'internal-boundary-filter-review.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    output_sha256=hashlib.sha256(data).hexdigest(),
    volume_and_point_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
    volume_connectivity_and_coordinates_byte_unchanged=True,
    removed_internal_boundary_faces=dict(removed),
    scope='Internal wall-marker faces removed by volume-face incidence. Original preserved; independent exterior and orientation verification still required.',
    engineering_accepted=False), indent=2))
print('Removed internal wall-marker faces:', dict(removed))
