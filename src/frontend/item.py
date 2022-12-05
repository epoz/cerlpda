from shared import *

check_lg = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-lg" viewBox="0 0 16 16">
  <path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/>
</svg>"""

clipboard = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-clipboard" viewBox="0 0 24 24">
    <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
    <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
</svg>"""


def citable_uri_click(event):
    event.preventDefault()
    navigator.clipboard.writeText("https://pda.cerl.org/id/" + document.objId)
    event.target.innerHTML = check_lg

    def reset_contents():
        event.target.innerHTML = "Copy URI to clipboard"

    setTimeout(reset_contents, 1000)


async def save_comment_click(event):
    event.preventDefault()
    txt = document.getElementById("commentInput").value
    if len(txt) < 2:
        return
    h = __new__(Headers)
    h.append("Content-Type", "application/json")
    result = await fetch(
        "/comment/",
        {
            "method": "POST",
            "credentials": "same-origin",
            "headers": h,
            "body": JSON.stringify({"txt": txt, "obj_id": document.objId}),
        },
    )
    response = await result.json()
    document.location.reload()


async def delete_comment_click(event):
    event.preventDefault()
    rowid = find_attr_parents(event.target, "data-rowid")
    if len(rowid) < 1:
        return
    h = __new__(Headers)
    h.append("Content-Type", "application/json")
    result = await fetch(
        "/comment/delete/" + rowid,
        {
            "method": "POST",
            "credentials": "same-origin",
            "headers": h,
        },
    )
    response = await result.json()
    document.location.reload()


async def on_delete_item(event):
    if window.confirm("Please confirm deletion of this item, do you want to continue?"):
        result = await fetch(
            "/id/" + document.objId, {"method": "DELETE", "credentials": "same-origin"}
        )
        if result.status == 200:
            document.location = "/"
        else:
            alert("This deletion not allowed")


def init():
    delete_button = document.getElementById("delete")
    if delete_button:
        delete_button.addEventListener("click", on_delete_item)
    document.getElementById("citable_uri").addEventListener("click", citable_uri_click)
    document.getElementById("saveComment").addEventListener("click", save_comment_click)
    for d in document.querySelectorAll(".deleteComment"):
        d.addEventListener("click", delete_comment_click)


window.addEventListener("load", init)
