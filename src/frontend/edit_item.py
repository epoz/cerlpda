title = document.getElementById("title")
imprint = document.getElementById("imprint")
author = document.getElementById("author")
shelfmark = document.getElementById("shelfmark")


def find_attr_parents(element, attr):
    val = element.getAttribute(attr)
    if val and len(val) > 0:
        return val
    parent = element.parentElement
    if parent:
        return find_attr_parents(parent, attr)


async def source_url(event):
    event.preventDefault()
    if document.source_url_bounce > 0:
        clearTimeout(document.source_url_bounce)
    document.source_url_bounce = setTimeout(do_source_url, 750)


async def do_source_url():
    source_url_spinner = document.getElementById("source_url_spinner")
    source_url_spinner.style.display = "block"

    value = document.getElementById("source_url").value
    # An example HPB URL looks like: http://hpb.cerl.org/record/DE-604.VK.BV012108280
    if value.find("//hpb.cerl.org/record/") > 0:
        tmp = value.split("//hpb.cerl.org/record/")
        if len(tmp) > 1:
            result = await fetch(
                "https://data.cerl.org/_external/hpb_search?query=pica.cid=" + tmp[1]
            )
            response = await result.json()
            source_url_spinner.style.display = "none"
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
        source_url_spinner.style.display = "none"
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
    source_url_spinner.style.display = "none"
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


async def modal_click_handler(event):
    field = event.target.getAttribute("data-field")
    value = event.target.getAttribute("data-value")
    target = event.target.getAttribute("data-target")
    if field and value:
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
    "_": "Unknown",
}


def set_the(field, dest, is_modal=False):
    if field not in document.obj:
        return
    elem = document.querySelector(dest)
    val = document.obj[field][0]
    if field.endswith("_CERLID"):
        tmp = val.split("|")
        val = tmp[1]
    elif field == "LANG":
        val = LANGUAGES[val]
    if is_modal:
        elem.innerHTML = val
    else:
        elem.value = val


async def init():
    document.getElementById("source_url").addEventListener("keyup", source_url)
    for item in document.querySelectorAll(".ct_modal_search"):
        item.addEventListener("keyup", modal_search_handler)
    for item in document.querySelectorAll(".modal"):
        item.addEventListener("click", modal_click_handler)
    for item in document.querySelectorAll(".dropdown-item"):
        item.addEventListener("click", dropdown_click_handler)

    if document.objId:
        result = await fetch("/id/" + document.objId + ".json")
        document.obj = await result.json()
        set_the("URL_WEBPAGE", "#source_url")
        set_the("CAPTION", "#caption")
        set_the("TITLE", "#title")
        set_the("PERSON_AUTHOR", "#author")
        set_the("IMPRINT", "#imprint")
        set_the("TEXT", "#transcription")
        set_the("SHELFMARK", "#shelfmark")
        set_the("DATE_ORIG", "#date")
        set_the("WIDTH", "#width")
        set_the("HEIGHT", "#height")
        # set_the("", "#")
        set_the("INSTIT_CERLID", "#institution", True)
        set_the("TYPE_INS", "#kindofprovenance", True)
        set_the("PAGE", "#location_source", True)
        set_the("LANG", "#language", True)
        set_the("TECHNIQUE", "#technique", True)


window.addEventListener("load", init)
