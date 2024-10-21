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
            similars_result = await fetch("/fragments/similar/" + hash_filename)
            similars = await similars_result.text()
            document.getElementById("image_thumbnails").innerHTML = similars

        else:
            document.getElementById("image_thumbnails").innerHTML = response.detail

    except:
        fileupload_spinner.style.display = "none"
    fileupload_spinner.style.display = "none"


async def init():
    document.getElementById("filechooser").addEventListener("change", filechosen)


window.addEventListener("load", init)
