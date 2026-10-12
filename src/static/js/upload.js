async function filechosen(event) {
  // post the file to /api/upload
  // and show the images similar to the returned hash_filename
  const fileuploadSpinner = document.getElementById("fileupload_spinner");
  fileuploadSpinner.style.display = "block";
  try {
    const filechooser = document.getElementById("filechooser");
    const img = filechooser.files[0];
    const formData = new FormData();
    formData.append("file", img);
    const result = await fetch("/api/upload", {
      method: "POST",
      credentials: "same-origin",
      body: formData,
    });
    const response = await result.json();
    if ("hash_filename" in response) {
      const similarsResult = await fetch(
        "/fragments/similar/" + response.hash_filename
      );
      const similars = await similarsResult.text();
      document.getElementById("image_thumbnails").innerHTML = similars;
    } else {
      document.getElementById("image_thumbnails").innerHTML = response.detail;
    }
  } finally {
    fileuploadSpinner.style.display = "none";
  }
}

function init() {
  document.getElementById("filechooser").addEventListener("change", filechosen);
}

window.addEventListener("load", init);
