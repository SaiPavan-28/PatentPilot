import asyncio
import httpx

async def test():
    query = {"_text_phrase": {"patent_abstract": "aspirin"}}
    payload = {
        "q": query,
        "f": ["patent_number", "patent_title"],
        "o": {"per_page": 5}
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                "https://api.patentsview.org/patents/query",
                json=payload
            )
            print("Status:", resp.status_code)
            print("Response:", resp.text[:200])
        except Exception as e:
            print("Error:", e)

asyncio.run(test())
