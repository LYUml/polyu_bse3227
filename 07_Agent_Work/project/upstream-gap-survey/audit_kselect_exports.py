"""Read-only source/native-export audit; no replacement of source PDF labels."""
from decimal import Decimal as D
import hashlib
import html
import json
import math
from pathlib import Path
from pypdf import PdfReader
from bsa.terminal_performance import calculate

ROOT=Path(__file__).resolve().parents[3]
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
OUT=ROOT/'07_Agent_Work/runs/kselect-export-audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exports=[ROOT/'05_Calculations'/n for n in ['k-select sd-01 maximum.pdf','k-select 1400 performance.pdf']]
pdf=ROOT/'07_Agent_Work/project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf'
catalogue=ROOT/'07_Agent_Work/project/bse3227-terminal-source/catalogue-source-bound.json'
lookup=ROOT/'07_Agent_Work/runs/current-agent-hvac-package/workflow/terminal-lookup/terminal-results.json'
inputs={str(p):sha(p) for p in [*exports,pdf,catalogue,lookup,Path(__file__)]}
text=PdfReader(exports[0]).pages[0].extract_text()
assert all(s in text for s in ['1400','50 fpm','Throw Feet','Throw m:','Performance at Specified Airflow'])
data=json.loads(catalogue.read_text());assert data['source_sha256']==sha(pdf)
# All nine Pt values and existing Ps/flow/throw/NC columns visually inspected
# on original B1-12. Retain the immutable original transcription separately.
pts=[1.4,5.7,12.8,22.7,35.5,51.1,69.5,90.8,114.9]
assert len(data['rows'])==len(pts)
rows=[dict(r,total_pressure_Pa=pt) for r,pt in zip(data['rows'],pts)]
source=json.loads(lookup.read_text());terminal=next(t for t in source['terminals'] if t['id']=='SD-01')
case=terminal['directions']['east']['cases']
q=D(str(case['maximum']['flow_L_s']))
cfm_L_s=D('.3048')**3*1000/60
flow_cfm=q/cfm_L_s
assert D('279.5')<=flow_cfm<=D('280.5')
point=calculate(rows,float(q))
weight=(q-D(132))/D(33)
for key,independent in [('total_pressure_Pa',D('22.7')+weight*D('12.8')),('static_pressure_Pa',D('12.8')+weight*D('7.1'))]:
    assert math.isclose(point[key],float(independent),rel_tol=1e-12,abs_tol=0)
# Selected native export cell read from inspected page; table says feet while
# its specified-airflow summary says metres with the same numerical value.
export_cfm=D(280);export_throw=D(14);export_pressure=D('.09')
ft_to_m=D('.3048');wc_to_Pa=D('249.08891') # Conventional inch water at4C.
throw_ft_interval=[float((export_throw-D('.5'))*ft_to_m),float((export_throw+D('.5'))*ft_to_m)]
catalogue_throw_interval=[4.15,4.25] # Published metric4.2m to0.1m precision.
assert max(throw_ft_interval[0],catalogue_throw_interval[0])<=min(throw_ft_interval[1],catalogue_throw_interval[1])
assert not D('13.5')<=D(str(point['T025_m']))<=D('14.5')
pressure_interval=[float((export_pressure-D('.005'))*wc_to_Pa),float((export_pressure+D('.005'))*wc_to_Pa)]
assert pressure_interval[0]<=point['total_pressure_Pa']<=pressure_interval[1]
assert not pressure_interval[0]<=point['static_pressure_Pa']<=pressure_interval[1]
# Preserve the observed octave-band discrepancy, without declaring an acoustic
# tolerance or interpolating NC into a new accepted value.
sound_export=[40,35,36,36,26,12];sound_printed=[40,35,36,35,26,12]
sound_diff=[a-b for a,b in zip(sound_export,sound_printed)]
review=dict(terminal='SD-01',model='1400',neck_in=8,module_in=[24,24],
    design_flow_L_s=float(q),design_flow_CFM=float(flow_cfm),export_flow_CFM=280,
    export_flow_L_s=float(export_cfm*cfm_L_s),export_matches_integer_CFM_rounding=True,
    catalogue_total_pressure_Pa=point['total_pressure_Pa'],catalogue_static_pressure_Pa=point['static_pressure_Pa'],
    native_pressure_display_in_wc=.09,native_pressure_display_interval_Pa=pressure_interval,
    native_pressure_matches_catalogue_total_at_display_precision=True,native_pressure_matches_static=False,
    pressure_reference_interpretation='Numerical correspondence to catalogue Pt; export field itself says only Pressure,w.c. Do not assert software documentation of its definition.',
    export_table_throw_value=14,export_table_throw_unit='ft',export_summary_throw_value=14.,export_summary_throw_unit='m',
    throw_labels_consistent=False,summary_throw_metres_accepted=False,
    table_throw_converted_m=float(export_throw*ft_to_m),catalogue_interpolated_T025_m=point['T025_m'],
    table_throw_matches_catalogue_at_published_display_precision=True,
    octave_band_difference_from_nearby_printed_point_dB=sound_diff,acoustic_agreement_verified=False,
    minimum_native_export_available=False,ADPI_verified=False,fan_pressure_complete=False,design_accepted=False,
    original_sources_modified=False,source_pages_visually_inspected=True,inputs=inputs)
review['independent_decimal_pressure_checks_match']=True
assert all(sha(Path(p))==h for p,h in inputs.items())
(OUT/'review.json').write_text(json.dumps(review,indent=2))
safe={k:v for k,v in review.items() if k!='inputs'}
(AGENT/'docs/evidence/kselect-export-audit.json').write_text(json.dumps(safe,indent=2))
(ROOT/'05_Calculations/KSelect_Export_Check.json').write_text(json.dumps(safe,indent=2))
paragraphs=[
    'Existing native K-Select export audit; separate manufacturer comparison, not an accepted diffuser selection or complete fan duty.',
    f"SD-01 design flow is {float(q):.6f} L/s ({float(flow_cfm):.6f} CFM). Export280CFM is consistent with integer display rounding.",
    f"At the source design flow the existing bounded catalogue method gives Pt={point['total_pressure_Pa']:.4f} Pa and Ps={point['static_pressure_Pa']:.4f} Pa. The native0.09inch-water display corresponds numerically to Pt at its two-decimal precision, and differs from Ps. Its label alone does not document the pressure definition. Do not add Pt and Ps together.",
    f"The native table explicitly labels throw as feet and gives14. The same page summary labels14.0as metres. These labels conflict. The table value converts to4.2672m and is consistent with the archival catalogue at its published precision. The summary14metres value is rejected for downstream design; original exports remain unchanged.",
    'At the nearby published279CFM point, NC20 matches the export display but octave band5 differs by1dB. Neither exact acoustic agreement nor a permissible acoustic tolerance is established. Native minimum-flow export and numerical ADPI verification remain pending.',
    'Basis: visually inspected native export and archival Krueger2012 B1-12,1400/51400,600x600mm panel,8-inch neck,no damper,horizontal isothermal50FPM throw. Catalogue pressure interpolation remains a declared piecewise-linear approximation. This audit does not approve the installed geometry, room load, manufacturer correspondence, room acoustics or complete engineering design.'
]
report='<!doctype html><html lang="en"><meta charset="utf-8"><title>Diffuser Export Review</title><style>body{font:16px/1.6 Arial;max-width:950px;margin:35px auto;padding:20px;color:#24343d}p{margin:20px 0}</style><h1>Diffuser Export Review</h1>'+''.join('<p>'+html.escape(p)+'</p>' for p in paragraphs)+'</html>'
(ROOT/'05_Calculations/Diffuser Export Review.html').write_text(report,encoding='utf-8')
print(json.dumps(safe,indent=2))
