import asyncio,json,os,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
repo=Path.cwd();root=Path(r'C:\Users\lyuml-win\Desktop\polyu_bse3227');here=Path(__file__).resolve().parent
async def main():
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server'],cwd=str(repo),env={**os.environ,'BSA_PROJECT_ROOT':str(root)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   args=dict(source='07_Agent_Work/runs/source-compound-network',out='07_Agent_Work/runs/mcp-native-network-analysis')
   response=await session.call_tool('bsa_run_native_network_analysis',args,read_timeout_seconds=timedelta(seconds=1200));assert not response.isError,str(response);run=response.structuredContent
   assert run['fitting_path_count']==76 and run['original_requirement_count']==33 and run['outlet_path_count']==20 and not run['design_accepted']
   (here/'network-execution-summary.json').write_text(json.dumps(run,indent=2));print('Actual MCP native graph execution complete:76 fitting paths,33 requirements,20 outlet paths',flush=True)
   response=await session.call_tool('bsa_inspect_native_network_analysis',dict(out=args['out']),read_timeout_seconds=timedelta(seconds=1200));assert not response.isError,str(response);checked=response.structuredContent
   assert checked['integrity_pass'] and {k:v for k,v in checked.items() if k!='integrity_pass'}==run
   (here/'network-inspection-summary.json').write_text(json.dumps(checked,indent=2));print('Independent actual MCP inspection agrees exactly; integrity passes, engineering remains pending',flush=True)
asyncio.run(main())
