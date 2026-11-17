"""Source-calibrated Q-squared diagnostic, not a replacement physical correlation."""
import asyncio
from decimal import Decimal as D
from datetime import timedelta
import hashlib
import html
import importlib.metadata
import inspect
import json
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
from bsa.manufacturer_adpi import catalogue
from bsa.terminal_performance import calculate
from fluids.numerics import interp

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
TOOLKIT=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit')
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
WORK=ROOT/'07_Agent_Work';OUT=WORK/'runs/terminal-pressure-source-envelope-reviewed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CFM_TO_LPS=D('.3048')**3*1000/60
PA_PER_WC=D('249.08891')

async def main():
    source=WORK/'project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf'
    assert sha(source)=='073c639219b28068a0c8190a926d493e42a12c0918db464ee8439c55a3994aef'
    # Actual visually reviewed B1-12,8inch,24x24,no damper,IP columns.
    qs=list(map(D,['70','140','209','279','349','419','489','559','628']))
    ps=list(map(D,['.006','.023','.051','.091','.142','.205','.279','.365','.461']))
    half=D('.0005')
    lower=max((p-half)/q**2 for p,q in zip(ps,qs));upper=min((p+half)/q**2 for p,q in zip(ps,qs))
    assert 0<lower<=upper
    coefficient=(lower+upper)/2
    assert all(p-half<=coefficient*q*q<=p+half for p,q in zip(ps,qs))
    pdfs=[(112.,TOOLKIT/'local/auto-112-v2/performance.pdf'),
          (280.,ROOT/'05_Calculations/k-select sd-01 maximum.pdf'),
          (300.,TOOLKIT/'local/auto-300-v7/performance.pdf')]
    lookup=WORK/'runs/current-agent-hvac-package/workflow/terminal-lookup/terminal-results.json'
    method_files=[Path(inspect.getsourcefile(f)) for f in [catalogue,calculate,interp]]
    native=[];pins={str(p):sha(p) for p in [source,Path(__file__),lookup,*method_files,*(TOOLKIT/'cli_anything/kselect'/n for n in ['server.py','core.py','service.py'])]}
    assert importlib.metadata.version('fluids')=='1.3.1' and importlib.metadata.version('mcp')=='1.30.0'
    params=StdioServerParameters(command=str(TOOLKIT/'.venv/Scripts/python.exe'),args=['-m','cli_anything.kselect.server'],cwd=TOOLKIT)
    async with stdio_client(params) as streams:
        async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=55)) as session:
            await session.initialize()
            cap=json.loads((await session.call_tool('get_capabilities',{})).content[0].text);assert cap['version']=='0.1.1'
            # Independent native values are not used to select/calibrate k.
            for cfm,pdf in pdfs:
                result=json.loads((await session.call_tool('verify_result',dict(pdf=str(pdf),airflow=cfm))).content[0].text)
                assert result['ok'] and all(result['checks'].values()),result
                assert result['report']['sha256']==sha(pdf)
                selected=D(str(result['report']['selected']['pressure_in_wc']))
                prediction=coefficient*D(str(cfm))**2
                matches=selected-D('.005')<=prediction<=selected+D('.005')
                assert matches
                pins[str(pdf)]=sha(pdf)
                native.append(dict(flow_CFM=cfm,export_total_pressure_in_wc=float(selected),
                    quadratic_diagnostic_pressure_in_wc=float(prediction),fits_assumed_nearest_0_01_display=matches,
                    independent_MCP_checks=result['checks'],pdf_sha256=sha(pdf)))
    rows=catalogue(source)['8'];terminals=json.loads(lookup.read_text())['terminals'];assert len(terminals)==80
    operating=[]
    for terminal in terminals:
        cases=next(iter(terminal['directions'].values()))['cases']
        for name in ['maximum','minimum']:
            q_lps=D(str(cases[name]['flow_L_s']));cfm=q_lps/CFM_TO_LPS
            assert qs[0]<=cfm<=qs[-1]
            values=[float(c*cfm**2*PA_PER_WC) for c in [lower,coefficient,upper]]
            linear=calculate(rows,float(q_lps))['total_pressure_Pa']
            operating.append(dict(terminal=terminal['id'],condition=name,flow_L_s=float(q_lps),
                source_calibrated_quadratic_diagnostic_Pa=values[1],source_rounding_only_interval_Pa=[values[0],values[2]],
                previous_catalogue_linear_Pa=linear,linear_minus_diagnostic_Pa=linear-values[1]))
    assert len(operating)==160
    assert all(sha(Path(p))==h for p,h in pins.items())
    OUT.mkdir(exist_ok=False)
    pins[str(lookup)]=sha(lookup)
    summary=dict(source_rows_reconciled=9,native_held_out_points=3,held_out_pressure_displays_match=True,
        fluids_version='1.3.1',client_mcp_version='1.30.0',external_toolkit_version='0.1.1',
        operating_cases=160,source_flow_bounds_CFM=[70,628],quadratic_coefficient_in_wc_per_CFM_squared=str(coefficient),
        coefficient_source_rounding_interval=[str(lower),str(upper)],
        maximum_linear_minus_diagnostic_Pa=max(x['linear_minus_diagnostic_Pa'] for x in operating),
        minimum_linear_minus_diagnostic_Pa=min(x['linear_minus_diagnostic_Pa'] for x in operating),
        source_rounding_is_not_measurement_uncertainty=True,
        constant_quadratic_coefficient_is_explicit_diagnostic_assumption=True,
        source_definition_url='https://www.krueger-hvac.com/file/9261/GRD_Engineering.pdf',
        production_pressure_method_replaced=False,native_software_rerun=False,
        pressure_budget_complete=False,ADPI_verified=False,design_accepted=False)
    (OUT/'study.json').write_text(json.dumps(dict(summary=summary,native_checks=native,operating_points=operating,inputs=pins),indent=2))
    (AGENT/'docs/evidence/terminal-pressure-envelope.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'05_Calculations/Terminal_Pressure_Interpolation_Check.json').write_text(json.dumps(summary,indent=2))
    headings=['Terminal','Condition','L/s','Existing linear Pt Pa','Quadratic diagnostic Pt Pa','Source rounding only Pa']
    tr=[]
    for x in operating:
        cells=[x['terminal'],x['condition'],f"{x['flow_L_s']:.3f}",f"{x['previous_catalogue_linear_Pa']:.4f}",f"{x['source_calibrated_quadratic_diagnostic_Pa']:.4f}",f"{x['source_rounding_only_interval_Pa'][0]:.4f} to {x['source_rounding_only_interval_Pa'][1]:.4f}"]
        tr.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in cells)+'</tr>')
    text='<!doctype html><html lang="en"><meta charset="utf-8"><title>Terminal Pressure Interpolation Review</title><style>body{font:15px/1.5 Arial;max-width:1150px;margin:30px auto;padding:20px;color:#24343d}table{border-collapse:collapse}th,td{border:1px solid #ccd6dd;padding:7px}</style><h1>Terminal Pressure Interpolation Review</h1>'
    text+='<p>Separate diagnostic; existing production pressures and original designs remain unchanged. One constant coefficient in P=kQ² fits all nine printed source Pt rows within their0.001inch-water rounding. Calibrated from archival catalogue only; three independently MCP-verified native points at112,280,300CFM agree with assumed0.01inch-water display rounding. Native data are held out from coefficient calibration.</p><p>This explains a possible interpolation source of the minimum-flow discrepancy; it does not prove the software internal equation or actual installed resistance. The constant coefficient and nearest display rounding are explicit assumptions. Bounds reflect source rounding only, not experimental uncertainty, manufacturing variation, Reynolds effects, installation or source/software edition equivalence. No extrapolation, NC interpolation, ADPI acceptance or complete fan duty follows. Parallel terminal pressures must not be summed.</p>'
    text+='<table><tr>'+''.join('<th>'+h+'</th>' for h in headings)+'</tr>'+''.join(tr)+'</table></html>'
    (ROOT/'05_Calculations/Terminal Pressure Interpolation Review.html').write_text(text,encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print(json.dumps([x for x in operating if x['terminal']=='SD-01'],indent=2))

asyncio.run(main())
