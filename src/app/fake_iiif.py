# https://iiif.io/api/image/2.1/
# http://www.example.org/image-service/abcd1234/full/full/0/default.jpg

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .config import UPLOADS_PATH, SITE_URI
import os
from .main import app
import pyvips
import traceback
import httpx


async def get_image(filename):
    filepath = os.path.join(UPLOADS_PATH, filename)
    filepath = filepath.replace(".jpg", "")
    if not os.path.exists(filepath):
        r = httpx.get(f"https://iiif.arkyves.org/{filename}/full/full/0/default.jpg")
        if r.status_code == 200:
            open(filepath, "wb").write(r.content)
        else:
            raise HTTPException(status_code=404, detail=f"Image [{filename}] not found")
    image = pyvips.Image.new_from_file(filepath, access="sequential")
    return image


@app.get(
    "/iiif/2/{filename}/{region}/{size}/{rotation}/{quality}.{format}",
    response_class=Response,
    include_in_schema=False,
)
async def imageapi(
    request: Request,
    filename: str,
    region: str,
    size: str,
    rotation: str,
    quality: str,
    format: str,
):
    image = await get_image(filename)

    try:
        # first do region crop
        if region.find(",") > 0:
            x, y, w, h = list(map(int, region.split(",")))
            if w > (image.width - x):
                w = image.width - x
            if h > (image.height - y):
                h = image.height - y
            cropped = image.crop(x, y, w, h)
        else:
            cropped = image
        scale = 1
        if size.find(",") > 0:
            nw, nh = size.split(",")
            if len(nw) > 0:
                scale = int(nw) / image.width
            elif len(nh) > 0:
                scale = int(nh) / image.height
        elif size.startswith("pct:"):
            scale = int(size[4:]) / 100
        o = cropped.resize(scale)
        data = o.write_to_buffer(".jpg[Q=95]")
        return Response(data, media_type="image/jpeg")
    except:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="An error occurred serving this image",
        )


@app.get(
    "/iiif/2/{filename}/info.json",
    response_class=Response,
    include_in_schema=False,
)
async def info(request: Request, filename: str):

    image = await get_image(filename)

    tmp = {
        "profile": [
            "http://iiif.io/api/image/2/level2.json",
            {
                "supports": [
                    "canonicalLinkHeader",
                    "profileLinkHeader",
                    "mirroring",
                    "rotationArbitrary",
                    "sizeAboveFull",
                    "regionSquare",
                ],
                "qualities": ["default"],
                "formats": ["jpg"],
            },
        ],
        "protocol": "http://iiif.io/api/image",
        "sizes": [],
        "height": image.height,
        "width": image.width,
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": f"{SITE_URI}iiif/2/{filename}",
    }
    return JSONResponse(tmp)
