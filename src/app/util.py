import smtplib, json, pickle
import numpy as np
from email.message import EmailMessage
import databases, httpx
from .config import DATABASE_URL
from fastapi import HTTPException
from markupsafe import Markup
from urllib.parse import quote_plus
from markdown_it import MarkdownIt

database = databases.Database(DATABASE_URL)


def send_email(sender: str, receiver: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(body)
    s = smtplib.SMTP("localhost")
    s.send_message(msg)
    s.quit()


field_titles = {
    "OWNERS_CERLID": "Owner",
    "CAPTION": "Description",
    "TEXT": "Transcription",
    "PERSON_AUTHOR": "Author",
    "INSTIT_CERLID": "Institution",
    "SHELFMARK": "Shelfmark",
    "LOCATION_ORIG_CERLID": "Place of use",
    "OWNERS": "Former Owners",
    "PAGE": "Location",
    "TYPE_INS": "Type",
    "TECHNIQUE": "Technique",
    "WIDTH": "Width",
    "HEIGHT": "Height",
    "TITLE": "Title",
    "COMMENT": "Notes",
    "DATE_ORIG": "Exact Date",
}


# A text filter to display a field including a heading if it exists in the object
# otherwise return a blank string
def TF(obj):
    def _TF(field):
        if field not in obj:
            return field, "", ""
        t = field_titles.get(field, "")
        v = " ".join(obj.get(field, []))
        return field, t, v

    return _TF


async def get(objid):
    row = await database.fetch_one(
        "SELECT obj FROM source WHERE id = :id", values={"id": objid}
    )

    if not row:
        raise HTTPException(status_code=404)

    obj = {}
    incoming = await load(row[0])

    # Remove all fields with empty lists or strings
    for k, v in incoming.items():
        tmp = [vv for vv in v if len(str(vv)) > 0]
        if len(tmp) > 0:
            obj[k] = tmp

    # fetch any annotations
    for row in await database.fetch_all(
        "SELECT rowid, user, value, timestamp FROM annotation WHERE field = 'COMMENT'  AND uid = :uid",
        values={"uid": objid},
    ):
        obj.setdefault("ANNOT", []).append(
            (row["rowid"], row["user"], row["value"], row["timestamp"])
        )

    for row in await database.fetch_all(
        "SELECT rowid, user, value, timestamp FROM annotation WHERE field = 'ZOOM'  AND uid = :uid ORDER BY rowid DESC",
        values={"uid": objid},
    ):
        obj.setdefault("_ZOOM", []).append((row["value"], json.loads(row["value"])))
        break  # only the latest zoom is needed

    # Fetch the instances
    if len(obj.get("INSTANCES", [])) > 0:

        exemplar = obj.get("EXEMPLAR", [None])[0]

        instance_ids = ",".join(
            f"'{instance}'" for instance in obj.get("INSTANCES", [])
        )
        instance_objs = await database.fetch_all(
            f"SELECT obj FROM source WHERE id IN ({instance_ids})"
        )
        instance_objs = [json.loads(row[0]) for row in instance_objs]
        if len(instance_objs) > 0:
            obj["_instances"] = instance_objs

    return obj


async def load(obj_string):
    obj = json.loads(obj_string)
    # if this is a provenance object, also fetch its details?
    exemplar = obj.get("EXEMPLAR", [None])[0]
    if exemplar:
        exemplar = await get(exemplar)
        for k, v in exemplar.items():
            if k not in obj:
                obj[k] = v

    return obj
    # Some fields, have IDs in them, filter them.
    # for k, v in obj.copy().items():
    #     if k in ("LOCATION_ORIG_CERLID", "OWNERS_CERLID", "INSTIT_CERLID"):
    #         obj[k] = [x.split("|")[-1].strip(" .,()") for x in obj[k]]
    # return obj


# A jinja filter to strip CERLIDs from a field
def strip_cerlid(value):
    if type(value) != str:
        return ""
    tmp = value.split("|")
    if len(tmp) < 2:
        return value
    cerlid = tmp[0]
    rest = "|".join(tmp[1:])
    return rest


# A Jinja filter to turn a | separated value into a CERL databases links
def to_link(uri, value):
    tmp = value.split("|")
    if len(tmp) < 2:
        return value
    cerlid = tmp[0]
    rest = "|".join(tmp[1:])
    return Markup(f"<a target='_cerl' href='{uri}{cerlid}'>{rest}</a>")


def cerl_holdinst(value):
    return to_link("https://data.cerl.org/holdinst/", value)


def cerl_thesaurus(value):
    return to_link("https://data.cerl.org/thesaurus/", value)


def owner_or_unknown(value):
    if value is None:
        return "Unidentified 🎈"
    values = value.split("|")
    if len(values) != 2:
        return "Unidentified 🎈"
    return values[1]


def to_paras(value):
    tmp = [f"<p class='notespara'>{v}</p>" for v in value.split("\n")]
    return Markup("".join(tmp))


def ic(values):
    params = [f"notation={quote_plus(v.strip(' '))}" for v in values]
    r = httpx.get("https://iconclass.org/json?" + "&".join(params))
    if r.status_code == 200:
        data = r.json()
        return data.get("result", [])
    return []


def markdown(value):
    m = MarkdownIt()
    return Markup(m.render(value))


def cosine_distance(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return 1 - dot_product / (norm_a * norm_b)


async def similar_to_image(animage: str):
    query = "SELECT filename, vecbuf FROM embeddings"
    embeddings_query = await database.fetch_all(query)
    embeddings = {}
    toget = None
    for row in embeddings_query:
        uid = row[0]
        vecbuf = row[1]
        vec = pickle.loads(vecbuf)
        if uid.startswith(animage):
            toget = vec
        else:
            embeddings[uid] = vec

    if toget is not None:
        closest_match = list(
            sorted(embeddings.items(), key=lambda x: cosine_distance(toget, x[1]))
        )
    else:
        closest_match = []

    matched_images = ",".join([f"'{x[0]}'" for x in closest_match[:10]])
    query = f"SELECT source.id, json_each.value FROM source, json_each(source.obj, '$.URL_IMAGE') WHERE json_each.value in ({matched_images})"
    matched_objs = {}
    for x in await database.fetch_all(query):
        matched_objs[x[1]] = await get(x[0])
    matched_objs_batch = [
        matched_objs[mi[0]] for mi in closest_match[:10] if mi[0] in matched_objs
    ]  # do this convoluted way to preserve the matched order, upgrade to Voyager or other ANN needed later
    return matched_objs_batch
