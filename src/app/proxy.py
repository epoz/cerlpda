from fastapi import FastAPI, Request
from starlette.responses import Response
import httpx
from .main import app

SOURCE_HOST = "pda.cerl.org"


@app.api_route(
    "/iiif/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(request: Request, path: str):
    url = f"https://{SOURCE_HOST}/iiif/{path}"
    client = httpx.AsyncClient()

    hdrs = [h for h in request.headers.raw if h[0] != b"host"]
    hdrs.append((b"host", SOURCE_HOST))

    response = await client.request(
        method=request.method,
        url=url,
        headers=hdrs,
        content=await request.body(),
    )

    # Create a response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
