"""Consume the user's existing pinned K-Select MCP, without duplicating its engine."""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters

TOOLKIT=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit')
PROJECT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
OUT=PROJECT/'07_Agent_Work/runs/kselect-mcp-project-minimum'

async def main():
    params=StdioServerParameters(command=str(TOOLKIT/'.venv/Scripts/python.exe'),args=['-m','cli_anything.kselect.server'],cwd=TOOLKIT)
    async with stdio_client(params) as streams:
        async with ClientSession(*streams,read_timeout_seconds=70) as session:
            await session.initialize()
            for tool in ['get_capabilities','get_status']:
                result=await session.call_tool(tool,{})
                data=json.loads(result.content[0].text)
                print(json.dumps({tool:data},ensure_ascii=True),flush=True)
                if tool=='get_status' and not data.get('ok'):return
            if '--calculate' not in sys.argv:return
            lookup=PROJECT/'07_Agent_Work/runs/current-agent-hvac-package/workflow/terminal-lookup/terminal-results.json'
            terminal=next(t for t in json.loads(lookup.read_text())['terminals'] if t['id']=='SD-01')
            q=terminal['directions']['east']['cases']['minimum']['flow_L_s']
            request=dict(airflow=q,airflow_unit='l/s',model='1400',neck_in=8,module='24x24',border='F23 T-Bar',output_directory=str(OUT))
            result=await session.call_tool('calculate_performance',request)
            data=json.loads(result.content[0].text)
            print(json.dumps({'calculate_performance':data},ensure_ascii=True),flush=True)
            if not data.get('ok'):return
            pdf=data['report']['path']
            verification=await session.call_tool('verify_result',{k:v for k,v in request.items() if k!='output_directory'}|{'pdf':pdf})
            replay=json.loads(verification.content[0].text)
            assert replay['ok'],replay
            assert replay['report']['sha256']==data['report']['sha256']
            (OUT/'project-mcp-replay.json').write_text(json.dumps(dict(request=request,result=data,verification=replay),indent=2))
            print(json.dumps({'independent_mcp_verify':True,'pdf':pdf,'sha256':data['report']['sha256']}),flush=True)

asyncio.run(main())
