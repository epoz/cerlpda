import { findAttrParents } from "./shared.js";

const checkLg = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-lg" viewBox="0 0 16 16">
  <path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/>
</svg>`;

const jsonHeaders = { "Content-Type": "application/json" };

async function checkedByEditorClick(event) {
  await fetch("/api/checked/" + document.objId, {
    method: "POST",
    credentials: "same-origin",
    headers: jsonHeaders,
    body: JSON.stringify({ obj_id: document.objId }),
  });
}

function citableUriClick(event) {
  event.preventDefault();
  const target = event.target;
  navigator.clipboard.writeText("https://pda.cerl.org/id/" + document.objId);
  target.innerHTML = checkLg;
  setTimeout(() => {
    target.innerHTML = "Copy URI to clipboard";
  }, 1000);
}

async function saveCommentClick(event) {
  event.preventDefault();
  const txt = document.getElementById("commentInput").value;
  if (txt.length < 2) {
    return;
  }
  await fetch("/comment/", {
    method: "POST",
    credentials: "same-origin",
    headers: jsonHeaders,
    body: JSON.stringify({ txt: txt, obj_id: document.objId }),
  });
  document.location.reload();
}

async function deleteCommentClick(event) {
  event.preventDefault();
  const rowid = findAttrParents(event.target, "data-rowid");
  if (!rowid) {
    return;
  }
  await fetch("/comment/delete/" + rowid, {
    method: "POST",
    credentials: "same-origin",
    headers: jsonHeaders,
  });
  document.location.reload();
}

async function onDeleteItem(event) {
  if (window.confirm("Please confirm deletion of this item, do you want to continue?")) {
    const result = await fetch("/id/" + document.objId, {
      method: "DELETE",
      credentials: "same-origin",
    });
    if (result.status == 200) {
      document.location = "/";
    } else {
      alert("This deletion not allowed");
    }
  }
}

function init() {
  const deleteButton = document.getElementById("delete");
  if (deleteButton) {
    deleteButton.addEventListener("click", onDeleteItem);
  }

  const checkedByEditor = document.getElementById("checked_by_editor");
  if (checkedByEditor) {
    checkedByEditor.addEventListener("click", checkedByEditorClick);
  }

  document.getElementById("citable_uri").addEventListener("click", citableUriClick);
  document.getElementById("saveComment").addEventListener("click", saveCommentClick);
  for (const d of document.querySelectorAll(".deleteComment")) {
    d.addEventListener("click", deleteCommentClick);
  }
}

window.addEventListener("load", init);
