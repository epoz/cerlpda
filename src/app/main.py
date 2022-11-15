from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Depends, FastAPI, Request, HTTPException, File, UploadFile
from .config import ORIGINS, DATABASE_URL, HELP_PATH, UPLOADS_PATH
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jinja2 import Markup
from hashlib import md5
import databases, os, json, random, time
from urllib.parse import quote_plus
import markdown, httpx, openpyxl
from pydantic import BaseModel
from typing import List, Optional
from .util import (
    TF,
    load,
    strip_cerlid,
    get,
    cerl_thesaurus,
    cerl_holdinst,
    to_paras,
    ic,
    markdown,
)

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
from .fake_iiif import *


class Obj(BaseModel):
    ID: List[str]
    TYPE_INS: Optional[List[str]]
    INSTIT: Optional[List[str]]
    URL_IMAGE: Optional[List[str]]
    COMMENT: Optional[List[str]]
    TITLE: Optional[List[str]]
    TEXT: Optional[List[str]]
    IC: Optional[List[str]]
    WIDTH: Optional[List[str]]
    LANG: Optional[List[str]]
    DATE_ORIG_CENTURY: Optional[List[str]]
    TECHNIQUE: Optional[List[str]]
    DATE_ORIG: Optional[List[str]]
    LOCATION_ORIG: Optional[List[str]]
    HEIGHT: Optional[List[str]]
    URL_WEBPAGE: Optional[List[str]]
    PAGE: Optional[List[str]]
    OWNERS_CERLID: Optional[List[str]]
    LOCATION_ORIG_CERLID: Optional[List[str]]
    INSTIT_CERLID: Optional[List[str]]
    IMPRINT: Optional[List[str]]
    PERSON_AUTHOR: Optional[List[str]]
    SHELFMARK: Optional[List[str]]
    USAGE: Optional[List[str]]
    CAPTION: Optional[List[str]]
    LOCATION_INV: Optional[List[str]]
    IMPRESSUM: Optional[List[str]]
    PERSON_CONTRIBUTOR: Optional[List[str]]
    URL_SEEALSO: Optional[List[str]]
    UPLOADER: Optional[List[str]]
    CANYOUHELP: Optional[List[str]]
    TIMESTAMP: Optional[List[str]]


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 401:
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


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


@app.get(
    "/edit/{anid:str}",
    include_in_schema=False,
    dependencies=[Depends(authenticated_user)],
)
async def edit_item(request: Request, anid: str):
    if anid == "new":
        anid = "_"
        obj = {}
    else:
        obj = await get(anid)

    response = templates.TemplateResponse(
        "edit_item.html",
        {"request": request, "anid": anid, "obj": obj},
    )
    return response


@app.get("/id/{anid:str}.json", include_in_schema=False)
async def item_json(request: Request, anid: str):
    if anid == "_":
        return {"ID": ["_"]}
    obj = await get(anid)
    return obj


@app.get("/id/{anid:str}.raw", include_in_schema=False)
async def item_id_raw(request: Request, anid: str):
    obj = await get(anid)
    return render_obj_with(request, obj, "item_raw.html")


@app.get("/id/{anid:str}", include_in_schema=False)
async def item_id(request: Request, anid: str):
    obj = await get(anid)
    return render_obj_with(request, obj, "item.html")


@app.put("/id/{anid:str}")
async def api_save(anid: str, obj: Obj, user=Depends(authenticated_user)):
    new_obj = {}
    for k, v in obj.dict().items():
        if v:
            new_obj[k] = v
    new_obj.setdefault("TIMESTAMP", []).append(time.ctime())

    if anid == "_":
        tmp = "".join([random.choice("0123456789abcdef") for x in range(5)])
        new_obj["ID"] = [f"cerlpda_{tmp}"]
        r = await database.execute(
            "INSERT INTO source VALUES (:id, :obj)",
            values={"obj": json.dumps(new_obj), "id": new_obj["ID"][0]},
        )
    else:
        r = await database.execute(
            "INSERT INTO history SELECT :user, CURRENT_TIMESTAMP, id, obj FROM source WHERE id = :id",
            values={"user": user.username, "id": anid},
        )
        r = await database.execute(
            "UPDATE source SET obj = :obj WHERE id = :id",
            values={"obj": json.dumps(new_obj), "id": anid},
        )
    return {"ID": new_obj["ID"][0]}


class Comment(BaseModel):
    obj_id: str
    txt: str


@app.post("/comment")
async def comment(cmnt: Comment, user=Depends(authenticated_user)):
    r = await database.execute(
        "INSERT INTO annotation VALUES (:user, :uid, 'COMMENT', :value, datetime())",
        values={"user": user.username, "uid": cmnt.obj_id, "value": cmnt.txt},
    )
    return {"status": "OK"}


@app.post("/comment/delete/{rowid:str}")
async def delete_comment(
    request: Request, rowid: str, user=Depends(authenticated_user)
):
    r = await database.execute(
        "DELETE FROM annotation WHERE rowid = :rowid", values={"rowid": rowid}
    )
    return {"status": "OK"}


def render_obj_with(request: Request, obj, template_name):
    # Try to find the owner from the admin table
    tmp = list(filter(None, [get_user_fromdb(u) for u in obj.get("UPLOADER", [])]))
    if len(tmp) > 0:
        obj["UPLOADER"] = tmp

    templates.env.filters["cerl_thesaurus"] = cerl_thesaurus
    templates.env.filters["cerl_holdinst"] = cerl_holdinst
    templates.env.filters["to_paras"] = to_paras
    templates.env.filters["ic"] = ic
    templates.env.filters["markdown"] = markdown
    response = templates.TemplateResponse(
        template_name,
        {"request": request, "obj": obj, "TF": TF(obj)},
    )
    return response


async def fragments_modal_iconclass(request: Request, q: str, size: int = 20):
    r = httpx.get("https://iconclass.org/api/search?q=" + quote_plus(q))
    if r.status_code == 200:
        result = r.json()
        ic_list = result.get("result", [])
        if len(ic_list) > 0:
            params = "&".join([f"notation={quote_plus(x)}" for x in ic_list])
            r = httpx.get(
                "https://iconclass.org/json?" + params,
                headers=httpx.Headers({"Content-Type": "application/json"}),
            )
            if r.status_code == 200:
                result = r.json()
                rows = []
                for ic in result.get("result", []):
                    notation = ic["n"]
                    txt = notation + " " + ic.get("txt", {}).get("en", "")
                    rows.append({"id": notation, "name": txt})

                return templates.TemplateResponse(
                    "fragments_modal_search.html",
                    {
                        "request": request,
                        "field": "IC",
                        "target": "#iconclass",
                        "data": rows,
                    },
                )


@app.get(
    "/fragments/modal_search",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def fragments_modal_search(
    request: Request, q: str = "", tipe: str = "institution", size: int = 20
):
    if tipe == "iconclass":
        return await fragments_modal_iconclass(request, q, size)

    field = "INSTIT_CERLID"
    target = "#institution"
    if tipe == "institution":
        url = f"https://data.cerl.org/holdinst/_search?size=100&query={quote_plus(q)}&format=json"
    elif tipe == "person":
        target = "#owners"
        field = "OWNERS_CERLID"
        url = f"https://data.cerl.org/thesaurus/_search?size=100&query=name%3A${quote_plus(q)}+AND+type%3A%28cnc+OR+cnp%29&format=json"
    elif tipe == "place":
        target = "#places"
        field = "LOCATION_ORIG_CERLID"
        url = f"https://data.cerl.org/thesaurus/_search?size=100&query=name%3A{quote_plus(q)}%20AND%20type:cnl&format=json"

    r = httpx.get(url)
    if r.status_code != 200:
        rows = [{"id": "unknown", "name": "Unknown"}]
    else:
        rr = r.json()
        rows = rr.get("rows", [])

    if tipe == "person":
        for row in rows:
            name = row["name_display_line"]
            if "year_start" in row or "year_end" in row:
                name = name + " ("
            if "year_start" in row:
                name = name + " " + row["year_start"][0]
            if "year_end" in row:
                if "year_start" in row:
                    name = name + " - "
                name = name + row["year_end"][0]
            if "year_start" in row or "year_end" in row:
                name = name + ")"
            row["name"] = name
    if tipe == "place":
        for row in rows:
            row["name"] = row["placeName"][0]

    response = templates.TemplateResponse(
        "fragments_modal_search.html",
        {
            "request": request,
            "field": field,
            "target": target,
            "data": rows,
        },
    )
    return response


@app.get("/fragments/search", response_class=HTMLResponse, include_in_schema=False)
async def fragments_search(
    request: Request, q: str = "", size: int = 50, tipe: str = "thumbs"
):
    batch = await api_search(q, size)
    batch["results"] = [(TF(b), b) for b in batch["results"]]

    if tipe == "thumbs":
        template_name = "fragments_search.html"
    else:
        template_name = "fragments_search_list.html"

    templates.env.filters["strip_cerlid"] = strip_cerlid
    response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "data": batch,
        },
    )
    return response


@app.get("/search")
async def search(request: Request, q: str = "", size: int = 20, page: int = 0):
    batch = await api_search(q, size, page)

    pages = round(batch["total"] / size)
    if pages > 10:
        pages = 10

    response = templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "data": batch,
            "size": size,
            "page": page,
            "pages": pages,
            "q": q,
        },
    )
    return response


@app.get("/canyouhelp", response_class=HTMLResponse, include_in_schema=False)
async def canyouhelp(request: Request, page: int = 0, size: int = 100):

    search_results = await database.fetch_all(
        "SELECT id FROM source WHERE length(canyouhelp) > 0 ORDER BY id"
    )
    batch = await fetch(search_results, size, page=page)

    pages = round(batch["total"] / size)

    response = templates.TemplateResponse(
        "search.html",
        {"request": request, "data": batch, "size": size, "page": page, "pages": pages},
    )
    return response


@app.get("/api/search")
async def api_search(q: str, size: int = 20, page: int = 0):
    if not q:
        search_results = await database.fetch_all(
            "SELECT id FROM source WHERE id NOT IN (SELECT id FROM idx WHERE text MATCH 'Unidentified')"
        )
    else:
        query = "SELECT id FROM idx WHERE text MATCH :q ORDER BY rank"
        try:
            search_results = await database.fetch_all(query, values={"q": q})
        except sqlite3.OperationalError:
            return {"total": 0, "results": []}
    return await fetch(search_results, size, page, q == "")


async def fetch(search_results, size, page=0, shuffle=False):
    total = len(search_results)
    search_results = [f"'{row[0]}'" for row in search_results]

    batch = await database.fetch_all(
        "SELECT obj FROM source WHERE id in (%s)" % ", ".join(search_results)
    )
    batch = [load(x[0]) for x in batch]
    if shuffle:
        random.shuffle(batch)

    start = page * size

    return {"total": total, "results": batch[start : start + size]}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return b"AAABAAEAEBAAAAEAGABoAwAAFgAAACgAAAAQAAAAIAAAAAEAGAAAAAAAAAAAAEgAAABIAAAAAAAA\nAAAAAADY9/jY9/jK39+NkpK0tLXAwcK5urusq6uusbG7vbynqKmvs7SwtbTY+fnY9/jY9/jY9/jY\n+frs///b1dY9Li1pYWF1d3WhmZeXlZUbFBMaCgyIcXHp8vTd///X9vfY9/jY9/jX9/jY+vvi///x\n///r8fVhTk7///8AAADv8fH6///w///c///X+PnX9vfY9/jY9/jY9/jY9/jX9/jY+vvo///Iy8qD\nenp9cG/7///Z///f///k/f7h///W9vfY9/jY9/jY9/jY9/jY9/jX9vff///X6ed4dHV6c3Pv///w\n///i5uRtWlr6///W9/jY9/jY9/jY9/jY9/jY9/jX9vff//++wsKzq6uXiIaWh4VRQUB0c3M/MzP/\n///a///Y9/jY9/jY9/jY9/jY9/jX9vfc///IzsyRhITh2dqjpKSDhYOWkZJgXVuolJPc///Y9/jY\n9/jY9/jX9vfX9/jW9vfZ//////9+c3Wcm5mzoqV9e3snJSdpUVHg29vb///Y9/jY9/jX9vfX+frm\n///t///////Gzc0xJib///+hn56+urrh39/n///j///Y+frY9/jY9/ja///0///u7u1AKymCdHT2\n/f5vaGb/9fW5s7O2uLby+frx7+/2///f///Y9/jY9/ji//+Kd3VdUVGnqalmZWVcXV13c3N2c3PF\nwMBIREQVExMoGRl6bWvp///Y9/jY9/je///LxMJoW11sbW2DhIWKjIuTkpJTVVVdXl6yr69maGgy\nLy/x8fHg///Y9/jY9/je///+///MwsOAgYGXkZFraWh7enlFRUVHR0dvbnBub21pZmjYycnt///Y\n9/jY9/jo//+OfHtnYmKJhIZUUlNeXmDHw8V1dXV6e3uMi4xhYGBIRUQ/MC/z///Y9/jY9/jq//+e\ngIB1bm1+fn2UkJFMR0ehn58NCwmsrqxWUVFnWli3srL1///i///Y9/jY9/jY+PnV5+fBxsaNjI2T\nlJSurq6OkZGrq6ubnZ2an5/R3d3b+vvY9/jX9vfY9/gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n"


@app.post("/api/upload", include_in_schema=True)
async def post_upload(file: UploadFile = File(...), user=Depends(authenticated_user)):
    if UPLOADS_PATH:
        file_name = file.filename
        if file_name.lower().split(".")[-1] not in (
            "jpeg",
            "jpg",
        ):
            raise HTTPException(
                status_code=500,
                detail=f"Only jpg image files are allowed, looks like this filename: {file_name} is not one of them",
            )
        contents = await file.read()
        hash_filename = md5(contents).hexdigest() + ".jpg"
        timestamp = str(time.time())
        open(os.path.join(UPLOADS_PATH, hash_filename), "wb").write(contents)
        meta = {
            "username": user.username,
            "file_size": len(contents),
            "file_name": file_name,
            "hash_filename": hash_filename,
            "timestamp": timestamp,
        }
        open(os.path.join(UPLOADS_PATH, f"{hash_filename}.{timestamp}"), "w").write(
            json.dumps(meta)
        )
        return meta
    raise HTTPException(
        status_code=500, detail="An UPLOADS_PATH has not been configured on the server"
    )


@app.get("/api/download/excel")
async def download_excel():
    data = await database.fetch_all("SELECT obj FROM source")
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Download"

    FIELDS = [
        "ID",
        "TYPE_INS",
        "INSTIT",
        "URL_IMAGE",
        "COMMENT",
        "TITLE",
        "TEXT",
        "IC",
        "WIDTH",
        "LANG",
        "DATE_ORIG_CENTURY",
        "TECHNIQUE",
        "DATE_ORIG",
        "LOCATION_ORIG",
        "HEIGHT",
        "URL_WEBPAGE",
        "PAGE",
        "OWNERS_CERLID",
        "LOCATION_ORIG_CERLID",
        "INSTIT_CERLID",
        "IMPRINT",
        "PERSON_AUTHOR",
        "SHELFMARK",
        "USAGE",
        "CAPTION",
        "LOCATION_INV",
        "IMPRESSUM",
        "PERSON_CONTRIBUTOR",
        "URL_SEEALSO",
        "UPLOADER",
        "CANYOUHELP",
        "NOTES",
    ]
    for i, f in enumerate(FIELDS):
        sheet.cell(row=1, column=i + 1).value = f
    for data_idx, row in enumerate(data):
        obj = json.loads(row[0])
        for i, f in enumerate(FIELDS):
            if f in obj:
                sheet.cell(row=data_idx + 2, column=i + 1).value = "\n".join(
                    [str(val) for val in obj.get(f, [])]
                )

    d = openpyxl.writer.excel.save_virtual_workbook(wb)
    ymdhhss = time.strftime("%Y-%m-%d_%H:%M")
    r = Response(
        d,
        media_type="application/vnd.ms-excel",
        headers={
            "Content-Disposition": f'attachment; filename="cerlpda_{ymdhhss}.xlsx"'
        },
    )
    return r


@app.get("/api/download/dmp")
async def download_dmp():
    data = await database.fetch_all("SELECT obj FROM source")
    buf = []
    for x in data:
        for k, v in json.loads(x[0]).items():
            tmp = "\n; ".join(["\n ".join(str(vv).split("\n")) for vv in v])
            buf.append(f"{k} {tmp}")
        buf.append("$")
    r = Response("\n".join(buf), media_type="text/plain")
    return r


@app.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def listview(request: Request, page: int = 0, size: int = 100):

    batch = await database.fetch_all("SELECT obj FROM source ORDER BY id")
    batch = [json.loads(x[0]) for x in batch]

    templates.env.filters["strip_cerlid"] = strip_cerlid
    response = templates.TemplateResponse(
        "list.html",
        {"request": request, "data": batch},
    )
    return response


@app.get("/r/{u:path}")
async def redirector(request: Request, u: str):
    return RedirectResponse(f"https://arkyves.org/r/{u}")
