import smtplib
from email.message import EmailMessage


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
