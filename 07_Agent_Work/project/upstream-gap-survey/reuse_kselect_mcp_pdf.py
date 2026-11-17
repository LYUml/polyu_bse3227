"""Verify existing toolkit-native PDF against actual project flow via MCP."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters

TOOLKIT=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit')
PROJECT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
OUT=PROJECT/'07_Agent_Work/runs/kselect-mcp-existing-minimum'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

async def main():
    pdf=TOOLKIT/'local/auto-112-v2/performance.pdf'
    parent=TOOLKIT/'local/auto-112-v2/result.json'
    lookup=PROJECT/'07_Agent_Work/runs/current-agent-hvac-package/workflow/terminal-lookup/terminal-results.json'
    terminal=next(t for t in json.loads(lookup.read_text())['terminals'] if t['id']=='SD-01')
    q=terminal['directions']['east']['cases']['minimum']['flow_L_s']
    assert sha(pdf)==json.loads(parent.read_text())['report']['sha256']
    pins={str(p):sha(p) for p in [pdf,parent,lookup,Path(__file__),*(TOOLKIT/'cli_anything/kselect'/n for n in ['server.py','core.py','service.py'])]}
    params=StdioServerParameters(command=str(TOOLKIT/'.venv/Scripts/python.exe'),args=['-m','cli_anything.kselect.server'],cwd=TOOLKIT)
    async with stdio_client(params) as streams:
        async with ClientSession(*streams,read_timeout_seconds=55) as session:
            await session.initialize()
            cap=json.loads((await session.call_tool('get_capabilities',{})).content[0].text)
            assert cap['ok'] and cap['version']=='0.1.1'
            request=dict(pdf=str(pdf),airflow=q,airflow_unit='l/s',model='1400',neck_in=8,module='24x24',border='F23 T-Bar')
            result=json.loads((await session.call_tool('verify_result',request)).content[0].text)
            assert result['ok'] and all(result['checks'].values()),result
            assert result['report']['sha256']==sha(pdf)
    assert all(sha(Path(p))==h for p,h in pins.items())
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(pdf,OUT/'Minimum Flow Native Performance.pdf')
    record=dict(transport='MCP stdio',toolkit_version=cap['version'],toolkit_commit='3eecd3710e976927c4b7c639900e833d12150453',
        native_software_rerun=False,existing_native_result_reused=True,request=request,result=result,inputs=pins,
        ADPI_verified=False,design_accepted=False)
    (OUT/'review.json').write_text(json.dumps(record,indent=2))
    print(json.dumps({k:record[k] for k in ['transport','toolkit_version','native_software_rerun','existing_native_result_reused']}|dict(checks=result['checks'],selected=result['report']['selected'],si=result['report']['si'],warnings=result['report'].get('warnings')),indent=2))

asyncio.run(main())
