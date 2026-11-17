import asyncio,json,os,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/Users/lyuml-win/Desktop/building-services-agent');B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
async def main():
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server','--autocad','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe','--graphviz',str(ROOT/'tools/freecad-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/bin/dot.exe')],cwd=str(ROOT),env={**os.environ,'BSA_PROJECT_ROOT':str(B)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize();args=dict(project='07_Agent_Work/project/general-drawing/source-ifc-system-graph.json',out='07_Agent_Work/runs/general-drawing-ifc-native-system')
   drawn=await session.call_tool('bsa_draw_document',args,read_timeout_seconds=timedelta(seconds=180));assert not drawn.isError,str(drawn)
   checked=await session.call_tool('bsa_inspect_drawing_document',args,read_timeout_seconds=timedelta(seconds=180));assert not checked.isError,str(checked);assert checked.structuredContent==drawn.structuredContent
   r=drawn.structuredContent;assert r['native_reopen_pass'] and r['graph']['nodes']==118 and r['graph']['edges']==117 and r['ifc_topology']['ports']==255
   (B/args['out']/'mcp-review.json').write_text(json.dumps(dict(result=r,same_inspection_result=True,desktop_existing_connection_reloaded=False),indent=2));print('118nodes/117edges extracted IFC topology generic MCP PASS')
asyncio.run(main())
