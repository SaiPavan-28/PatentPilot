import asyncio
from backend.retrieval.pubchem_client import retrieve_pubchem_patents

async def test():
    # Use Aspirin SMILES
    res = await retrieve_pubchem_patents("CC(=O)OC1=CC=CC=C1C(=O)O")
    print(res)

asyncio.run(test())
