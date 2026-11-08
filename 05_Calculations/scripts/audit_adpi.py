"""Audit model-specific ADPI classification without extrapolating load tables."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '05_Calculations/data'
rows = list(csv.DictReader((DATA / 'diffusers_v01.csv').open()))
audit = []
for row in rows:
    # ASHRAE 2015 Ch57 Table3: circular pattern uses closest wall/intersecting jet.
    length = min(float(row[f'L_{d}_m']) for d in ('w', 'e', 's', 'n'))
    maximum = float(row['max_T025_m']) / length
    minimum = float(row['min_T025_m']) / length
    audit.append({
        'id': row['id'], 'L_closest_m': length,
        'max_T025_over_L': maximum, 'min_T025_over_L': minimum,
        'within_2015_60W_range_0p7_1p3': .7 <= maximum <= 1.3,
        'within_2015_125W_range_0p5_1p5': .5 <= maximum <= 1.5,
        'within_2019_round_25W_range_0p4_3p2_at_min': .4 <= minimum <= 3.2,
        'within_2019_round_50W_range_0p5_3p2_at_min': .5 <= minimum <= 3.2,
    })
result = {
    'revision': 'v01 independent classification audit',
    'model': 'Krueger 1400, circular-pattern Type 3 per manufacturer a1-11',
    'load_max_sensible_W_m2': 90, 'load_min_sensible_W_m2': 36,
    'status': 'NOT ACCEPTED: maximum-load ADPI unverified',
    'interpretation': [
        'Retire the generic louvered 1.0–3.4 screen as the model-specific acceptance test.',
        'Table-range comparisons below are diagnostic, not interpolated ADPI predictions.',
        '90 W/m2 is not a tabulated test load in either reference.',
        '36 W/m2 lies between 2019 25/50 W/m2 cases, but matching both ranges is not a measured ADPI.',
        'Original catalogue throws and geometrical assumptions remain subject to their recorded limitations.',
    ],
    'max_outside_both_2015_bracket_ranges': [r['id'] for r in audit if not r['within_2015_60W_range_0p7_1p3'] and not r['within_2015_125W_range_0p5_1p5']],
    'rows': audit,
}
(DATA / 'adpi_classification_audit_v01.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))
