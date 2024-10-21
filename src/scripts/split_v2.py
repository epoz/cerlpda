import sqlite3, json, os, sys, random
from rich import print

DB = sqlite3.connect(sys.argv[1])
DB.executescript(
    """CREATE TABLE IF NOT EXISTS embeddings (filename TEXT PRIMARY KEY, vecbuf BLOB);
    ALTER TABLE source ADD COLUMN tipe as (json_extract(obj, '$.TIPE[0]'))"""
)

DB.execute("ALTER TABLE source ADD COLUMN TIPE TEXT")

data = {}
for id, obj in DB.execute("select id, obj from source"):
    data[id] = json.loads(obj)

# Go through data and move objects to new "provenance" object, removing fields that are in the list: [PERSON_AUTHOR, IMPRINT, URL_IMAGE, SHELFMARK, INSTIT, INSTIT_CERLID, URL_IMAGE, URL_CERL, TITLE]
provmarks = {}
details = {}
unknown_bib = {}
images = {}
detail_fields = [
    "PERSON_AUTHOR",
    "IMPRINT",
    "SHELFMARK",
    "INSTIT",
    "LOCATION",
    "LOCATION_ORIG",
    "LOCATION_ORIG_CERLID",
    "PAGE",
    "INSTIT_CERLID",
    "URL_WEBPAGE",
    "URL_IMAGE",
    "URL_CERL",
    "TITLE",
    "DATE_ORIG",
    "DATE_ORIG_CENTURY",
]
retain_fields = ["TIMESTAMP", "UPLOADER"]
for id, o in data.items():
    main = o.copy()
    detail = o.copy()
    if "URL_WEBPAGE" not in o:
        unknown_bib[id] = o
    images[id] = o.get("URL_IMAGE", None)
    for k in detail_fields:
        if k in retain_fields:
            continue
        if k in main:
            del main[k]
    for detail_key in list(detail.keys()).copy():
        if detail_key in retain_fields:
            continue
        if detail_key not in detail_fields:
            del detail[detail_key]
    main["TIPE"] = ["provenance"]
    detail_id = "cerlpda_" + "".join(
        [random.choice("0123456789abcdef") for x in range(8)]
    )
    if detail_id in provmarks:
        print("!", detail_id)

    detail["ID"] = [detail_id]
    detail["TIPE"] = ["provenance_instance"]
    detail["PROVENANCE"] = [id]
    details[detail_id] = detail

    main["INSTANCES"] = [detail_id]
    main["EXEMPLAR"] = [detail_id]
    provmarks[id] = main
print("unknown bib: ", len(unknown_bib), "data length:", len(data))
print(len(provmarks), "provmarks", len(details), "details")

new_ones = list(details.values()) + list(provmarks.values())

DB.execute(
    "INSERT INTO history SELECT 'eposthumus@gmail.com', CURRENT_TIMESTAMP, id, obj FROM source"
)
DB.execute("DELETE FROM source")
for obj in new_ones:
    DB.execute(
        "INSERT INTO source VALUES (?, ?)",
        (
            obj["ID"][0],
            json.dumps(obj),
        ),
    )
DB.commit()
