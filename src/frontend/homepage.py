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
    result = await fetch("/fragments/search?q=" + searchbox.value)
    response = await result.text()
    searchresults.innerHTML = response
    document.imagesLoaded(document.querySelector(".grid"), update_grid)


async def searchbox_keyup(event):
    event.preventDefault()
    if document.searchbounce > 0:
        clearTimeout(document.searchbounce)
    document.searchbounce = setTimeout(do_search, 500)


async def result_handler(event):
    anid = find_attr_parents(event.target, "anid")
    if anid:
        event.preventDefault()
        document.location = "/id/" + anid


async def init():
    searchbox.addEventListener("keyup", searchbox_keyup)
    if showrandom:
        showrandom.addEventListener("click", searchbox_keyup)
    searchresults.addEventListener("click", result_handler)
    searchbox.focus()


window.addEventListener("load", init)
