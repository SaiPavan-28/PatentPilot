import asyncio
from backend.retrieval.agent import retrieve_patents
import logging
logging.basicConfig(level=logging.INFO)

async def test():
    patents = await retrieve_patents('CC(=O)OC1=CC=CC=C1C(=O)O', 'COX', 'Pain')
    print(f'Total patents retrieved: {len(patents)}')
    for p in patents[:5]:
        print(f'- {p.get("patent_number")}: {p.get("title")}')

if __name__ == "__main__":
    asyncio.run(test())
