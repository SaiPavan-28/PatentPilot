import asyncio
from backend.retrieval.patentsview_client import search_patents_by_text

async def test():
    res = await search_patents_by_text(["aspirin"])
    print(res)

asyncio.run(test())
