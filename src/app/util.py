import smtplib, json
from email.message import EmailMessage
import databases
from .config import DATABASE_URL
from fastapi import HTTPException
from jinja2 import Markup

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
    "PERSON_AUTHOR": "Source",
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
}


# A text filter to display a field including a heading if it exists in the object
# otherwise return a blank string
def TF(obj):
    def _TF(field):
        if field not in obj:
            return "", ""
        t = field_titles.get(field, "")
        v = " ".join(obj.get(field, []))
        return t, v

    return _TF


async def get(objid):
    row = await database.fetch_one(
        "SELECT obj FROM source WHERE id = :id", values={"id": objid}
    )

    if not row:
        raise HTTPException(status_code=404)

    obj = json.loads(row[0])
    return obj


def load(obj_string):
    obj = json.loads(obj_string)
    return obj
    # Some fields, have IDs in them, filter them.
    # for k, v in obj.copy().items():
    #     if k in ("LOCATION_ORIG_CERLID", "OWNERS_CERLID", "INSTIT_CERLID"):
    #         obj[k] = [x.split("|")[-1].strip(" .,()") for x in obj[k]]
    # return obj


# A jinja filter to strip CERLIDs from a field
def strip_cerlid(value):
    tmp = value.split("|")
    if len(tmp) < 2:
        return value
    cerlid = tmp[0]
    rest = "|".join(tmp[1:])
    return rest


# A Jinja filter to turn a | separated value into a CERL Thesarus link
def cerl_thesaurus(value):
    tmp = value.split("|")
    if len(tmp) < 2:
        return value
    cerlid = tmp[0]
    rest = "|".join(tmp[1:])
    return Markup(f"<a href='https://data.cerl.org/thesaurus/{cerlid}'>{rest}</a>")
