import asyncio,json,os,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/Users/lyuml-win/Desktop/building-services-agent');B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
async def main():
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server','--autocad','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe'],cwd=str(ROOT),env={**os.environ,'BSA_PROJECT_ROOT':str(B)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   tools=(await session.list_tools()).tools;assert {'bsa_draw_document','bsa_inspect_drawing_document'}<={x.name for x in tools}
   invalid=await session.call_tool('bsa_draw_document',dict(project='../outside.json',out='07_Agent_Work/runs/not-created-escape'));assert invalid.isError
   args=dict(project='07_Agent_Work/project/general-drawing/course-plan-text-revision.json',out='07_Agent_Work/runs/general-drawing-mcp-existing-dwg-loaded')
   drawn=await session.call_tool('bsa_draw_document',args,read_timeout_seconds=timedelta(seconds=180));assert not drawn.isError,str(drawn)
   checked=await session.call_tool('bsa_inspect_drawing_document',args);assert not checked.isError,str(checked);assert checked.structuredContent==drawn.structuredContent
   result=drawn.structuredContent;assert result['integrity_pass'] and result['native_reopen_pass'] and result['preservation']['edited_texts']==3
   output=B/args['out'];(output/'mcp-review.json').write_text(json.dumps(dict(result=result,escape_rejected=True,listed_tools=True,same_inspection_result=True,desktop_existing_connection_reloaded=False),indent=2));print(json.dumps(result))
asyncio.run(main())
