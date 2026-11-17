"""Conditional native/catalogue/curve comparison with explicit display uncertainty."""
from decimal import Decimal as D
import hashlib
import html
import json
from pathlib import Path
from bsa.manufacturer_adpi import catalogue,screen
from bsa.terminal_performance import calculate

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
WORK=ROOT/'07_Agent_Work'
RUN=WORK/'runs/kselect-mcp-existing-minimum'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((RUN/'review.json').read_text())
assert all(sha(Path(p))==h for p,h in record['inputs'].items())
native=record['result']['report'];assert native['sha256']==sha(RUN/'Minimum Flow Native Performance.pdf')
lookup=WORK/'runs/current-agent-hvac-package/workflow/terminal-lookup/terminal-results.json'
terminal=next(t for t in json.loads(lookup.read_text())['terminals'] if t['id']=='SD-01')
pdf=WORK/'project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf'
curves_path=WORK/'runs/manufacturer-adpi-native-curves/curves.json'
curves=json.loads(curves_path.read_text())
assert sha(curves_path)=='dc59a674eda24baeac6f0a8dd2e1f81034a6bf9a101972e086f23279e1ff737e'
assert curves['source_pdf_sha256']==sha(WORK/'project/adpi-manufacturer-study/GRD_Engineering.pdf')
flow=native['selected']['airflow_cfm'];effective=flow*.3048**3*1000/60
point=calculate(catalogue(pdf)['8'],effective)
q=D(str(effective));weight=(q-D(33))/D(33)
assert abs(D(str(point['total_pressure_Pa']))-(D('1.4')+weight*D('4.3')))<D('1e-12')
pressure_display=D(str(native['selected']['pressure_in_wc']))
pressure_interval=[float((pressure_display-D('.005'))*D('249.08891')),float((pressure_display+D('.005'))*D('249.08891'))]
pressure_matches=pressure_interval[0]<=point['total_pressure_Pa']<=pressure_interval[1]
assert not pressure_matches
directions=[]
for name,direction in terminal['directions'].items():
    L=direction['characteristic_length_m']
    for condition,feet,loads in [('maximum',14.,[40,60]),('minimum',native['selected']['throw_ft'],[20,40])]:
        low=(feet-.5)*.3048/L;high=(feet+.5)*.3048/L
        nominal=[dict(load_Btuh_ft2=load,**screen(curves,load,feet*.3048/L)) for load in loads]
        uncertainty=[]
        for load in loads:
            xs={low,high}
            for fragment in curves['fragments']:
                if fragment['load_Btuh_ft2']==load:xs.update(p[0] for p in fragment['points'] if low<p[0]<high)
            checks=[screen(curves,load,x) for x in sorted(xs)]
            uncertainty.append(dict(load_Btuh_ft2=load,all_sampled_bounds_and_knots_pass=all(x['status']=='paired_curve_threshold_met' for x in checks),
                minimum_stroke_margin_lower_ADPI=min((x['stroke_margin_lower_ADPI'] for x in checks if 'stroke_margin_lower_ADPI' in x),default=None),
                any_outside_source_domain=any(x['status']=='outside_published_curve_or_fragment_domain' for x in checks)))
        directions.append(dict(direction=name,condition=condition,diagnostic_L_m=L,nominal_ratio=feet*.3048/L,
            assumed_nearest_foot_display_ratio_interval=[low,high],nominal_paired_screen=nominal,display_uncertainty_screen=uncertainty))
assert all(all(x['status']=='paired_curve_threshold_met' for x in d['nominal_paired_screen']) for d in directions if d['condition']=='minimum')
assert any(not all(x['all_sampled_bounds_and_knots_pass'] for x in d['display_uncertainty_screen']) for d in directions if d['condition']=='minimum')
summary=dict(transport='MCP stdio',toolkit_version=record['toolkit_version'],toolkit_commit=record['toolkit_commit'],existing_native_PDF_reused=True,
    independent_MCP_checks_all_pass=all(record['result']['checks'].values()),minimum_native_export_available=True,
    design_minimum_L_s=record['request']['airflow'],effective_minimum_CFM=flow,effective_minimum_L_s=effective,
    native_throw_ft=native['selected']['throw_ft'],native_throw_m=native['si']['throw_m'],native_total_pressure_display_in_wc=float(pressure_display),
    native_pressure_display_rounding_interval_Pa=pressure_interval,catalogue_linear_total_pressure_at_effective_flow_Pa=point['total_pressure_Pa'],
    native_and_catalogue_linear_pressure_match_at_display_precision=pressure_matches,native_pressure_reference_confirmed_by_prior_UI_total_pressure_label=True,
    minimum_nominal_paired_curve_screen_passes_four_directions=True,minimum_nearest_foot_uncertainty_screen_passes_four_directions=False,
    characteristic_lengths_physically_accepted=False,display_rounding_interval_is_diagnostic_assumption=True,
    acoustic_NC_accepted=False,ADPI_verified=False,fan_pressure_complete=False,design_accepted=False,native_PDF_sha256=native['sha256'])
full=dict(summary=summary,directions=directions,inputs={str(p):sha(p) for p in [RUN/'review.json',lookup,pdf,curves_path,Path(__file__)]})
(RUN/'comparison.json').write_text(json.dumps(full,indent=2))
(AGENT/'docs/evidence/kselect-mcp-minimum.json').write_text(json.dumps(summary,indent=2))
(ROOT/'05_Calculations/KSelect_Minimum_Flow_Check.json').write_text(json.dumps(summary,indent=2))
paragraphs=[
    'Separate manufacturer comparison for SD-01. Existing native PDF from the user K-Select Agent Toolkit is reused and independently verified through MCP; no new native calculation is claimed.',
    f"Requested minimum flow {summary['design_minimum_L_s']:.6f} L/s is rounded by the toolkit to112CFM ({effective:.6f} L/s). Native configuration1400,8inch neck,24x24inch panel,F23T-Bar,50fpm,horizontal passes all seven request checks. The native PDF is actually rendered and inspected.",
    f"Native throw is8feet (2.4384m). Original report summary mislabels this as metres; the toolkit reconciles it to the feet table. The reported NC10 conflicts with the table dash, so usable NC remains unknown.",
    f"Native total pressure displays0.01inch water. Under an explicitly assumed nearest0.01display convention this represents {pressure_interval[0]:.6f}..{pressure_interval[1]:.6f} Pa, rather than a high-precision2.4908891Pa measurement. Archival catalogue linear interpolation at the same effective flow gives {point['total_pressure_Pa']:.6f} Pa, outside that interval. This discrepancy remains unresolved; no pressure method is silently replaced and no combined fan duty is accepted.",
    'Using the inherited conditional40percent load scenario and existing Type3 guide curves, the nominal8foot throw meets both20/40Btuh/ft2 curve screens for the four inherited characteristic lengths. Assuming nearest-foot rounding, the full display interval fails that paired screen in north/south directions. Maximum14foot throw remains outside the paired40/60curve domain. These are diagnostics only: characteristic-length applicability, actual thermal load, source/software correspondence and measured ADPI remain unverified.',
    'The existing rigid-network pressure study retains30conditional fitting paths and33numerical gaps. Terminal pressures must not be summed across parallel outlets or added as both Pt and Ps. No original course drawing, network, historical receipt or source PDF is modified.'
]
report='<!doctype html><html lang="en"><meta charset="utf-8"><title>Diffuser Minimum Flow Review</title><style>body{font:16px/1.6 Arial;max-width:950px;margin:35px auto;padding:20px;color:#24343d}</style><h1>Diffuser Minimum Flow Review</h1>'+''.join('<p>'+html.escape(p)+'</p>' for p in paragraphs)+'</html>'
(ROOT/'05_Calculations/Diffuser Minimum Flow Review.html').write_text(report,encoding='utf-8')
print(json.dumps(summary,indent=2))
