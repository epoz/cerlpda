from .config import DB_PATH_MB
import sqlite3
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from .main import app, templates


def escape(param):
    # As we need to use string formatting to access a table name, this leaves us open to SQL injection attacks :-(
    return "".join(
        [ch for ch in param.lower() if ch in "abcdefghijklmnopqrstuvwxyz0123456789_"]
    )


@app.get(
    "/xy/{projectname}/{x:float}_{y:float}",
    response_class=JSONResponse,
    include_in_schema=False,
)
async def xy(projectname: str, x: float, y: float):
    projectname = escape(projectname)
    db = sqlite3.connect(DB_PATH_MB)
    for row in db.execute(
        f"SELECT objuid FROM bounds_{projectname} WHERE x1 <= ? AND x2 >= ? AND y1 <= ? AND y2 >= ?",
        (x, x, y, y),
    ):
        obj_id = row[0]
        return {"obj_id": obj_id}

    raise HTTPException(status_code=404)


@app.get("/overview/")
async def overview(request: Request):
    return templates.TemplateResponse("overview.html", {"request": request})
