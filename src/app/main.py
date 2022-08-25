from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import Depends, FastAPI, Request, HTTPException, Query
from .config import ORIGINS, DATABASE_URL, HELP_PATH
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jinja2 import Markup
import databases, os, json
import markdown
from .util import TF

database = databases.Database(DATABASE_URL)

app = FastAPI(openapi_url="/openapi")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .am import *


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request):
    # Count the number of items in the database and display a total as welcome message
    row = await database.fetch_one("SELECT count(id) FROM source")
    total = row[0]

    response = templates.TemplateResponse(
        "homepage.html",
        {
            "request": request,
            "total": total,
        },
    )
    return response


@app.get("/help/{page}", response_class=HTMLResponse, include_in_schema=False)
async def help(request: Request, page: str):
    infilepath = os.path.join(HELP_PATH, f"{page}.md")
    if not os.path.exists(infilepath):
        raise HTTPException(status_code=404, detail=f"Page [{page}] not found")
    md = markdown.Markdown(
        output_format="html5", extensions=["nl2br", "meta", "attr_list", "tables"]
    )
    html = md.convert(open(infilepath).read())

    return templates.TemplateResponse(
        "help.html", {"request": request, "content": Markup(html)}
    )


@app.get("/canyouhelp", response_class=HTMLResponse, include_in_schema=False)
async def canyouhelp(request: Request):
    response = templates.TemplateResponse(
        "canyouhelp.html",
        {
            "request": request,
        },
    )
    return response


@app.get("/new", response_class=HTMLResponse, include_in_schema=False)
async def new_item(request: Request):
    response = templates.TemplateResponse(
        "new_item.html",
        {
            "request": request,
        },
    )
    return response


@app.get("/id/{anid:str}", include_in_schema=False)
async def item_id(request: Request, anid: str):
    row = await database.fetch_one(
        "SELECT obj FROM source WHERE id = :id", values={"id": anid}
    )

    if not row:
        raise HTTPException(status_code=404)

    obj = json.loads(row[0])
    # Some fields, have IDs in them, filter them.
    for k, v in obj.copy().items():
        if k in ("LOCATION_ORIG_CERLID", "OWNERS_CERLID", "INSTIT_CERLID"):
            obj[k] = [x.split("|")[-1].strip(" .,()") for x in obj[k]]

    # Try to find the owner from the admin table
    user = obj.get("OWNER")
    if user and len(user) > 0:
        user = get_user_fromdb(user[0])
        obj["OWNER"] = user
    else:
        del obj["OWNER"]

    response = templates.TemplateResponse(
        "item.html",
        {"request": request, "obj": obj, "TF": TF(obj)},
    )
    return response


@app.get("/fragments/search", response_class=HTMLResponse, include_in_schema=False)
async def fragments_search(request: Request, q: str = "", size: int = 20):
    batch = await api_search(q, size)
    response = templates.TemplateResponse(
        "fragments_search.html",
        {
            "request": request,
            "data": batch,
        },
    )
    return response


@app.get("/search")
async def search(request: Request, q: str = "", size: int = 20):
    batch = await api_search(q, size)
    response = templates.TemplateResponse(
        "search.html",
        {"request": request, "data": batch, "q": q},
    )
    return response


@app.get("/api/search")
async def api_search(q: str, size: int = 20):
    total = 0
    if not q:
        search_results = await database.fetch_all(
            "SELECT id FROM source ORDER BY random()"
        )
        total = len(search_results)
    else:
        query = "SELECT id FROM idx WHERE text MATCH :q ORDER BY rank"
        search_results = await database.fetch_all(query, values={"q": q})
        total = len(search_results)
    search_results = [f"'{row[0]}'" for row in search_results]

    batch = await database.fetch_all(
        "SELECT obj FROM source WHERE id in (%s)" % ", ".join(search_results)
    )
    batch = [json.loads(x[0]) for x in batch]
    return {"total": total, "results": batch[:size]}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return b"AAABAAEAEBAAAAEAGABoAwAAFgAAACgAAAAQAAAAIAAAAAEAGAAAAAAAAAAAAEgAAABIAAAAAAAA\nAAAAAADY9/jY9/jK39+NkpK0tLXAwcK5urusq6uusbG7vbynqKmvs7SwtbTY+fnY9/jY9/jY9/jY\n+frs///b1dY9Li1pYWF1d3WhmZeXlZUbFBMaCgyIcXHp8vTd///X9vfY9/jY9/jX9/jY+vvi///x\n///r8fVhTk7///8AAADv8fH6///w///c///X+PnX9vfY9/jY9/jY9/jY9/jX9/jY+vvo///Iy8qD\nenp9cG/7///Z///f///k/f7h///W9vfY9/jY9/jY9/jY9/jY9/jX9vff///X6ed4dHV6c3Pv///w\n///i5uRtWlr6///W9/jY9/jY9/jY9/jY9/jY9/jX9vff//++wsKzq6uXiIaWh4VRQUB0c3M/MzP/\n///a///Y9/jY9/jY9/jY9/jY9/jX9vfc///IzsyRhITh2dqjpKSDhYOWkZJgXVuolJPc///Y9/jY\n9/jY9/jX9vfX9/jW9vfZ//////9+c3Wcm5mzoqV9e3snJSdpUVHg29vb///Y9/jY9/jX9vfX+frm\n///t///////Gzc0xJib///+hn56+urrh39/n///j///Y+frY9/jY9/ja///0///u7u1AKymCdHT2\n/f5vaGb/9fW5s7O2uLby+frx7+/2///f///Y9/jY9/ji//+Kd3VdUVGnqalmZWVcXV13c3N2c3PF\nwMBIREQVExMoGRl6bWvp///Y9/jY9/je///LxMJoW11sbW2DhIWKjIuTkpJTVVVdXl6yr69maGgy\nLy/x8fHg///Y9/jY9/je///+///MwsOAgYGXkZFraWh7enlFRUVHR0dvbnBub21pZmjYycnt///Y\n9/jY9/jo//+OfHtnYmKJhIZUUlNeXmDHw8V1dXV6e3uMi4xhYGBIRUQ/MC/z///Y9/jY9/jq//+e\ngIB1bm1+fn2UkJFMR0ehn58NCwmsrqxWUVFnWli3srL1///i///Y9/jY9/jY+PnV5+fBxsaNjI2T\nlJSurq6OkZGrq6ubnZ2an5/R3d3b+vvY9/jX9vfY9/gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n"
