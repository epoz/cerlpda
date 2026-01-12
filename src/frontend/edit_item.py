from shared import *

title = document.getElementById("title")
imprint = document.getElementById("imprint")
author = document.getElementById("author")
shelfmark = document.getElementById("shelfmark")

REQUIRED_FIELDS = [
    "CAPTION",
    "INSTIT_CERLID",
    "SHELFMARK",
    "TYPE_INS",
    "IC",
]

FIELDS_MAP = {
    "URL_WEBPAGE": "#source_url",
    "CAPTION": "#caption",
    "TITLE": "#title",
    "PERSON_AUTHOR": "#author",
    "IMPRINT": "#imprint",
    "TEXT": "#transcription",
    "SHELFMARK": "#shelfmark",
    "DATE_ORIG": "#date",
    "WIDTH": "#width",
    "HEIGHT": "#height",
    "IC": "#iconclass",
    "INSTIT_CERLID": "#institution",
    "TYPE_INS": "#kindofprovenance",
    "PAGE": "#location_source",
    "LANG": "#language",
    "TECHNIQUE": "#technique",
    "OWNERS_CERLID": "#owners",
    "LOCATION_ORIG_CERLID": "#places",
}


def required_fields_filled():
    for field in REQUIRED_FIELDS:
        if field not in document.obj:
            return FIELDS_MAP[field]
        filled = filter(None, [len(val.strip(" ")) > 0 for val in document.obj[field]])
        if len(filled) < 1:
            return FIELDS_MAP[field]
    return True


async def source_url(event):
    event.preventDefault()
    if document.source_url_bounce > 0:
        clearTimeout(document.source_url_bounce)
    document.source_url_bounce = setTimeout(do_source_url, 750)


async def do_source_url():

    value = document.getElementById("source_url").value
    # An example HPB URL looks like: http://hpb.cerl.org/record/DE-604.VK.BV012108280
    if value.find("//hpb.cerl.org/record/") > 0:
        tmp = value.split("//hpb.cerl.org/record/")
        if len(tmp) > 1:
            result = await fetch(
                "https://data.cerl.org/_external/hpb_search?query=pica.cid=" + tmp[1]
            )
            response = await result.json()
            if response.hits > 0:
                data = response.rows[0]
                if data.title:
                    title.value = data.title
                if data.imprint:
                    imprint.value = data.imprint
                if data.author:
                    author.value = data.author
    # For MEI entries, we first need to retrieve the linked ISTC record and THEN do a ISTC lookup
    # entries look like: https://data.cerl.org/mei/02122152?format=json
    if value.find("//data.cerl.org/mei/") > 0:
        if value.find("format=json") < 0:
            value = value + "?format=json"
        url = value.replace("http://", "https://")
        result = await fetch(url)
        response = await result.json()
        if response.data:
            data = response.data
            if data.shelfmark:
                shelfmark.value = data.shelfmark
            if data.hostItemId:
                do_ISTC(
                    "https://data.cerl.org/istc/" + data.hostItemId + "?format=json"
                )
    # For ISTC lookups, they are like: https://data.cerl.org/istc/ia00070500
    if value.find("//data.cerl.org/istc/") > 0:
        do_ISTC(value)


async def do_ISTC(url):
    if url.find("format=json") < 0:
        url = url + "?format=json"
    url = url.replace("http://", "https://")
    result = await fetch(url)
    response = await result.json()
    if response.data:
        data = response.data
        if data.title:
            title.value = data.title
        if data.imprint:
            # The ISTC data has an object for imprint
            i = data.imprint[0]
            imprint.value = (
                i.imprint_place + " " + i.imprint_name + " " + i.imprint_date
            )
        if data.author:
            author.value = data.author


trash = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash3-fill" viewBox="0 0 16 16">
  <path d="M11 1.5v1h3.5a.5.5 0 0 1 0 1h-.538l-.853 10.66A2 2 0 0 1 11.115 16h-6.23a2 2 0 0 1-1.994-1.84L2.038 3.5H1.5a.5.5 0 0 1 0-1H5v-1A1.5 1.5 0 0 1 6.5 0h3A1.5 1.5 0 0 1 11 1.5Zm-5 0v1h4v-1a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5ZM4.5 5.029l.5 8.5a.5.5 0 1 0 .998-.06l-.5-8.5a.5.5 0 1 0-.998.06Zm6.53-.528a.5.5 0 0 0-.528.47l-.5 8.5a.5.5 0 0 0 .998.058l.5-8.5a.5.5 0 0 0-.47-.528ZM8 4.5a.5.5 0 0 0-.5.5v8.5a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5Z"/>
</svg>
"""


async def remove_val(event):
    val = find_attr_parents(event.target, "data-value")
    field = find_attr_parents(event.target, "data-field")
    dest = find_attr_parents(event.target, "data-dest")
    if val and field:
        NEW = [x for x in document.obj[field] if x != val]
        document.obj[field] = NEW
    set_the(field, dest, False, True)
    event.preventDefault()


async def remove_image(event):
    to_remove = find_attr_parents(event.target, "data-filename")
    if to_remove:
        URL_IMAGE = []
        for x in dict(document.obj).get("URL_IMAGE", []):
            if x != to_remove:
                URL_IMAGE.add(x)
        document.obj["URL_IMAGE"] = URL_IMAGE
        showthumbnails()
    event.preventDefault()


async def showthumbnails():
    thumbs = document.getElementById("image_thumbnails")
    thumbs.innerHTML = ""
    for x in dict(document.obj).get("URL_IMAGE", []):
        i = document.createElement("img")
        i.src = "/iiif/2/" + x + "/full/200,/0/default.jpg"
        i.style["margin-right"] = "4px"
        thumbs.appendChild(i)
        t = document.createElement("div")
        t.style.display = "inline"
        t.style["margin-right"] = "2vw"
        t.style.cursor = "pointer"
        t.innerHTML = trash
        t.setAttribute("data-filename", x)
        t.addEventListener("click", remove_image)
        thumbs.appendChild(t)


async def radio_choice(event):
    value = find_attr_parents(event.target, "data-value")
    dest = find_attr_parents(event.target, "data-dest")
    CURRENT = document.obj.get(dest, [])

    console.log(event.target.checked, dest, value)
    if event.target.checked:
        if value not in CURRENT:
            CURRENT.append(value)
            document.obj[dest] = CURRENT
    if not event.target.checked:
        if value in CURRENT:
            NEW = [x for x in CURRENT if x != value]
            document.obj[dest] = NEW


async def filechosen(event):
    # post the file to /api/upload
    # and set the returned hashfilename to the data here (if not already in the URL_IMAGE)
    fileupload_spinner = document.getElementById("fileupload_spinner")
    fileupload_spinner.style.display = "block"
    try:
        filechooser = document.getElementById("filechooser")
        img = filechooser.files[0]
        form_data = __new__(FormData)
        form_data.append("file", img)
        result = await fetch(
            "/api/upload",
            {"method": "POST", "credentials": "same-origin", "body": form_data},
        )
        response = await result.json()
        if "hash_filename" in response:
            hash_filename = response["hash_filename"]
            # Check if this returned hash is in the obj
            URL_IMAGE = document.obj.get("URL_IMAGE", [])
            if hash_filename not in URL_IMAGE:
                URL_IMAGE.append(hash_filename)
                document.obj["URL_IMAGE"] = URL_IMAGE
            showthumbnails()
        else:
            document.getElementById("image_thumbnails").innerHTML = response.detail

    except:
        fileupload_spinner.style.display = "none"
    fileupload_spinner.style.display = "none"


async def modal_click_handler(event):
    field = event.target.getAttribute("data-field")
    value = event.target.getAttribute("data-value")
    target = event.target.getAttribute("data-target")
    if field and value:
        # Certain fields are multi
        if field in ["OWNERS_CERLID", "LOCATION_ORIG_CERLID", "IC"]:
            CURRENT = document.obj.get(field, [])
            if value not in CURRENT:
                CURRENT.append(value)
            document.obj[field] = CURRENT
            set_the(field, target, False, True)
        else:
            document.obj[field] = [value]
            set_the(field, target, True)


async def dropdown_click_handler(event):
    value = find_attr_parents(event.target, "data-code")
    if not value:
        value = event.target.innerHTML
    field = find_attr_parents(event.target, "data-field")
    target = find_attr_parents(event.target, "data-target")

    if field and value:
        document.obj[field] = [value]
        if field == "PAGE":
            if value == "Page/Folio number":
                elem = document.querySelector(target)
                elem.value = ""
                elem.focus()
            else:
                set_the(field, target)

        else:
            set_the(field, target, True)
        event.preventDefault()


async def modal_search_handler(event):
    event.preventDefault()
    document.ct_tipe = event.target.getAttribute("ct_tipe")
    document.ct_value = event.target.value
    document.ct_target = event.target.getAttribute("ct_target")

    if document.modal_search_bounce > 0:
        clearTimeout(document.modal_search_bounce)
    document.modal_search_bounce = setTimeout(do_modal_search, 750)


async def do_modal_search():
    result = await fetch(
        "/fragments/modal_search?q="
        + encodeURI(document.ct_value)
        + "&tipe="
        + encodeURI(document.ct_tipe)
    )
    response = await result.text()
    document.getElementById(document.ct_target).innerHTML = response


LANGUAGES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "nl": "Dutch",
    "it": "Italian",
    "la": "Latin",
    "gr": "Greek",
    "he": "Hebrew",
    "ru": "Russian",
    "_": "Unknown",
}


def set_the(field, dest, is_modal=False, is_multi=False):
    if field not in document.obj:
        return
    elem = document.querySelector(dest)
    # special treatement for the url_seealso field
    if field == "URL_SEEALSO":
        if document.obj[field]:
            elem.innerHTML = "\n".join(document.obj[field])
        return
    if is_multi:
        elem.innerHTML = ""
    for val in document.obj[field]:
        showval = val
        if field.endswith("_CERLID"):
            tmp = val.split("|")
            showval = tmp[1]
        elif field == "LANG":
            showval = LANGUAGES[val]
        if is_modal:
            elem.innerHTML = showval
        elif is_multi:
            s = document.createElement("span")
            s.style.margin = "0 4px 0 0"
            s.innerHTML = showval
            elem.appendChild(s)
            t = document.createElement("div")
            t.style.display = "inline"
            t.style["margin-right"] = "2vw"
            t.style.cursor = "pointer"
            t.innerHTML = trash
            t.setAttribute("data-value", val)
            t.setAttribute("data-field", field)
            t.setAttribute("data-dest", dest)
            t.addEventListener("click", remove_val)
            elem.appendChild(t)
        else:
            elem.value = showval


def from_the(field, src):
    elem = document.querySelector(src)
    document.obj[field] = [elem.value]


def save_fields():
    from_the("URL_WEBPAGE", "#source_url")
    from_the("COMMENT", "#notes")
    from_the("CAPTION", "#caption")
    from_the("TITLE", "#title")
    from_the("PERSON_AUTHOR", "#author")
    from_the("IMPRINT", "#imprint")
    from_the("TEXT", "#transcription")
    from_the("SHELFMARK", "#shelfmark")
    from_the("DATE_ORIG", "#date")
    from_the("WIDTH", "#width")
    from_the("HEIGHT", "#height")
    from_the("PAGE", "#page")
    canyouhelp = document.querySelector("#canyouhelp")
    if canyouhelp.checked:
        document.obj["CANYOUHELP"] = [Date.now()]
    else:
        document.obj["CANYOUHELP"] = []
    # Handle the URL_SEEALSO field specially to only filter items that start with http
    document.obj["URL_SEEALSO"] = []  # default to empty, and only set if valid values
    url_seealso = document.getElementById("url_seealso")
    val = url_seealso.value
    if len(val) > 8:
        vals = [
            x
            for x in val.split("\n")
            if x.startswith("http://") or x.startswith("https://")
        ]
        if len(vals) > 0:
            document.obj["URL_SEEALSO"] = vals


async def savebutton_handler(event):
    event.preventDefault()

    save_fields()

    # clear all required fields first
    for afield in REQUIRED_FIELDS:
        elem = document.querySelector(FIELDS_MAP[afield])
        elem.style.border = "none"

    missing_field = required_fields_filled()
    if missing_field != True:
        elem = document.querySelector(missing_field)
        elem.style.border = "2px solid red"
        elem.focus()
        return

    anid = document.obj["ID"][0]
    h = __new__(Headers)
    h.append("Content-Type", "application/json")
    result = await fetch(
        "/id/" + anid,
        {
            "method": "PUT",
            "credentials": "same-origin",
            "headers": h,
            "body": JSON.stringify(document.obj),
        },
    )
    response = await result.json()
    document.location = "/id/" + response["ID"]


async def add_missing_item(event):
    data = {}  # "entry", "firstname", "nonsort", "addition"
    missing_tab = find_attr_parents(event.target, "data-missing")
    if missing_tab == "place":
        data["action"] = "add_place"
        tmp = document.getElementById("missing_place").value
        if len(tmp) < 2:
            return
        data["entry"] = tmp
        tmp = document.getElementById("missing_place_comment").value
        if len(tmp) > 0:
            data["notes"] = tmp
    if missing_tab == "person":
        data["action"] = "add_person"
        tmp = document.getElementById("missing_lastname").value
        if len(tmp) < 2:
            return
        data["entry"] = tmp
        for elem_name, key_name in [
            ["missing_firstname", "firstname"],
            ["missing_prefix", "nonsort"],
            ["missing_owner_comment", "notes"],
        ]:
            tmp = document.getElementById(elem_name).value
            if len(tmp) > 1:
                data[key_name] = tmp

    if missing_tab == "corporate":
        data["action"] = "add_corporate"
        data["entry"] = document.getElementById("missing_corporatebody").value
        data["notes"] = document.getElementById("missing_corporatebody_comment").value
    h = __new__(Headers)
    h.append("Content-Type", "application/json")
    result = await fetch(
        "/api/cerlthesaurus",
        {
            "method": "POST",
            "credentials": "same-origin",
            "headers": h,
            "body": JSON.stringify(data),
        },
    )
    response = await result.json()

    console.log("Added new " + missing_tab)


async def init():
    document.getElementById("source_url").addEventListener("keyup", source_url)
    document.getElementById("filechooser").addEventListener("change", filechosen)

    for item in document.querySelectorAll(".add_missing_item"):
        item.addEventListener("click", add_missing_item)
    for item in document.querySelectorAll(".ct_modal_search"):
        item.addEventListener("keyup", modal_search_handler)
    for item in document.querySelectorAll(".century_choice"):
        item.addEventListener("change", radio_choice)
    for item in document.querySelectorAll(".modal"):
        item.addEventListener("click", modal_click_handler)
    for item in document.querySelectorAll(".dropdown-item"):
        item.addEventListener("click", dropdown_click_handler)
    for button in document.querySelectorAll(".save_button"):
        button.addEventListener("click", savebutton_handler)

    if document.objId:
        result = await fetch("/id/" + document.objId + ".json")
        document.obj = await result.json()
        set_the("URL_WEBPAGE", "#source_url")
        set_the("COMMENT", "#notes")
        set_the("CAPTION", "#caption")
        set_the("TITLE", "#title")
        set_the("PERSON_AUTHOR", "#author")
        set_the("IMPRINT", "#imprint")
        set_the("TEXT", "#transcription")
        set_the("SHELFMARK", "#shelfmark")
        set_the("DATE_ORIG", "#date")
        set_the("WIDTH", "#width")
        set_the("HEIGHT", "#height")
        set_the("NOTES", "#notes")
        set_the("IC", "#iconclass", False, True)
        set_the("INSTIT_CERLID", "#institution", True)
        set_the("TYPE_INS", "#kindofprovenance", True)
        set_the("PAGE", "#page")
        set_the("LANG", "#language", True)
        set_the("TECHNIQUE", "#technique", True)
        set_the("OWNERS_CERLID", "#owners", False, True)
        set_the("LOCATION_ORIG_CERLID", "#places", False, True)
        set_the("URL_SEEALSO", "#url_seealso")
        showthumbnails()


window.addEventListener("load", init)
