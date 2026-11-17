"""Finite, source-bound layout comparison; never modifies delivery files."""
import json, hashlib
import csv
from pathlib import Path
from bsa.air_layout_study import evaluate_variant
from shapely.geometry import shape, Point

B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
P=B/'07_Agent_Work/project'
R=B/'07_Agent_Work/runs/course-diffuser-position-screen'
R.mkdir(exist_ok=False)
paths={'allocation':P/'bse3227-aligned-design-inputs/allocation.json',
       'boundary':P/'bse3227-column-row-candidate/office-boundary.geojson',
       'catalogue':P/'bse3227-terminal-source/catalogue-reviewed.json'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={k:sha(p) for k,p in paths.items()}
project=json.loads(paths['allocation'].read_text())
boundary=json.loads(paths['boundary'].read_text())
catalogue=json.loads(paths['catalogue'].read_text())
variants=[dict(id='existing',basis='Unchanged submitted positions',changes=[])]
# Preserve horizontal/vertical alignment by shifting complete source rows/columns.
for axis,coordinate in [(1,32.1),(0,92.425932)]:
    members=[t for t in project['terminals'] if abs(t['center_m'][axis]-coordinate)<1e-7]
    for delta in [-.15,-.10,-.05,.05,.10,.15]:
        changes=[]
        for t in members:
            xy=list(t['center_m']);xy[axis]+=delta
            changes.append(dict(id=t['id'],center_m=xy))
        variants.append(dict(id=f'axis{axis}_{delta:+.2f}',basis='Declared 50-150 mm complete-row/column perturbation; reallocate same total load',changes=changes))
summary=[]
for variant in variants:
    result=evaluate_variant(boundary,project,catalogue,variant,[.6,.6],[1,3.4])
    ratios=[c['ratio'] for row in result['cases'] for c in row['lookup']['cases'].values() if c['ratio'] is not None]
    row=dict(id=variant['id'],changes=variant['changes'],minimum_ratio=min(ratios),maximum_ratio=max(ratios),
             outside=len(result['panel_outside_boundary']),overlaps=len(result['panel_overlaps']),
             ratio_failures=result['diagnostic_ratio_cases_outside_range'],cell_ray_mismatches=result['cell_ray_mismatches'],
             selected=False,ADPI_verified=False)
    summary.append(row)
    (R/(variant['id']+'.json')).write_text(json.dumps(result,indent=2))
    print({k:v for k,v in row.items() if k!='changes'},flush=True)
assert pins=={k:sha(p) for k,p in paths.items()}
(R/'summary.json').write_text(json.dumps(dict(inputs=pins,variants=summary,
    scope='Catalogue classroom diagnostic only. New native K-Select, VAV routing, drawings and full engineering review required before adoption.',
    selected_variant=None,ADPI_verified=False),indent=2))
