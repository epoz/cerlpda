from shared import *

searchbox = document.getElementById("searchbox")
searchresults = document.getElementById("searchresults")
showrandom = document.getElementById("showrandom")


async def update_grid():
    grid = document.querySelector(".grid")
    if grid and grid.masonry:
        grid.masonry.reloadItems()
        grid.masonry.layout()


async def do_search():
    document.location = "/search?q=" + searchbox.value


async def do_search_suggest():
    console.log(".")


async def searchbox_keyup(event):
    event.preventDefault()
    if event.keyCode == 13:
        do_search()

    if document.searchbounce > 0:
        clearTimeout(document.searchbounce)
    document.searchbounce = setTimeout(do_search_suggest, 500)


async def result_handler(event):
    anid = find_attr_parents(event.target, "anid")
    if anid:
        event.preventDefault()
        document.location = "/id/" + anid


async def set_location_to_search(event):
    event.preventDefault()
    document.location = "/search"


async def init():
    searchbox.addEventListener("keyup", searchbox_keyup)
    if showrandom:
        showrandom.addEventListener("click", set_location_to_search)
    searchresults.addEventListener("click", result_handler)
    searchbox.focus()


window.addEventListener("load", init)
