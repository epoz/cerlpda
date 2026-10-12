import { findAttrParents } from "./shared.js";

const title = document.getElementById("title");
const imprint = document.getElementById("imprint");
const author = document.getElementById("author");
const shelfmark = document.getElementById("shelfmark");

const REQUIRED_FIELDS = ["CAPTION", "INSTIT_CERLID", "SHELFMARK", "TYPE_INS", "IC"];

const FIELDS_MAP = {
  URL_WEBPAGE: "#source_url",
  CAPTION: "#caption",
  TITLE: "#title",
  PERSON_AUTHOR: "#author",
  IMPRINT: "#imprint",
  TEXT: "#transcription",
  SHELFMARK: "#shelfmark",
  DATE_ORIG: "#date",
  WIDTH: "#width",
  HEIGHT: "#height",
  IC: "#iconclass",
  INSTIT_CERLID: "#institution",
  TYPE_INS: "#kindofprovenance",
  PAGE: "#location_source",
  LANG: "#language",
  TECHNIQUE: "#technique",
  OWNERS_CERLID: "#owners",
  LOCATION_ORIG_CERLID: "#places",
};

const LANGUAGES = {
  en: "English",
  de: "German",
  fr: "French",
  nl: "Dutch",
  it: "Italian",
  la: "Latin",
  gr: "Greek",
  he: "Hebrew",
  ru: "Russian",
  _: "Unknown",
};

const trash = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash3-fill" viewBox="0 0 16 16">
  <path d="M11 1.5v1h3.5a.5.5 0 0 1 0 1h-.538l-.853 10.66A2 2 0 0 1 11.115 16h-6.23a2 2 0 0 1-1.994-1.84L2.038 3.5H1.5a.5.5 0 0 1 0-1H5v-1A1.5 1.5 0 0 1 6.5 0h3A1.5 1.5 0 0 1 11 1.5Zm-5 0v1h4v-1a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5ZM4.5 5.029l.5 8.5a.5.5 0 1 0 .998-.06l-.5-8.5a.5.5 0 1 0-.998.06Zm6.53-.528a.5.5 0 0 0-.528.47l-.5 8.5a.5.5 0 0 0 .998.058l.5-8.5a.5.5 0 0 0-.47-.528ZM8 4.5a.5.5 0 0 0-.5.5v8.5a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5Z"/>
</svg>
`;

const jsonHeaders = { "Content-Type": "application/json" };

// The item being edited, loaded as JSON from the server in init()
document.obj = {};

// Returns true if all required fields have a value, otherwise the selector of the first missing one
function requiredFieldsFilled() {
  for (const field of REQUIRED_FIELDS) {
    const values = document.obj[field] || [];
    const filled = values.filter((val) => String(val).trim().length > 0);
    if (filled.length < 1) {
      return FIELDS_MAP[field];
    }
  }
  return true;
}

function sourceUrl(event) {
  event.preventDefault();
  if (document.source_url_bounce > 0) {
    clearTimeout(document.source_url_bounce);
  }
  document.source_url_bounce = setTimeout(doSourceUrl, 750);
}

async function doSourceUrl() {
  let value = document.getElementById("source_url").value;
  // An example HPB URL looks like: http://hpb.cerl.org/record/DE-604.VK.BV012108280
  if (value.indexOf("//hpb.cerl.org/record/") > 0) {
    const tmp = value.split("//hpb.cerl.org/record/");
    if (tmp.length > 1) {
      const result = await fetch(
        "https://data.cerl.org/_external/hpb_search?query=pica.cid=" + tmp[1]
      );
      const response = await result.json();
      if (response.hits > 0) {
        const data = response.rows[0];
        if (data.title) title.value = data.title;
        if (data.imprint) imprint.value = data.imprint;
        if (data.author) author.value = data.author;
      }
    }
  }
  // For MEI entries, we first need to retrieve the linked ISTC record and THEN do a ISTC lookup
  // entries look like: https://data.cerl.org/mei/02122152?format=json
  if (value.indexOf("//data.cerl.org/mei/") > 0) {
    if (value.indexOf("format=json") < 0) {
      value = value + "?format=json";
    }
    const url = value.replaceAll("http://", "https://");
    const result = await fetch(url);
    const response = await result.json();
    if (response.data) {
      const data = response.data;
      if (data.shelfmark) shelfmark.value = data.shelfmark;
      if (data.hostItemId) {
        doISTC("https://data.cerl.org/istc/" + data.hostItemId + "?format=json");
      }
    }
  }
  // For ISTC lookups, they are like: https://data.cerl.org/istc/ia00070500
  if (value.indexOf("//data.cerl.org/istc/") > 0) {
    doISTC(value);
  }
}

async function doISTC(url) {
  if (url.indexOf("format=json") < 0) {
    url = url + "?format=json";
  }
  url = url.replaceAll("http://", "https://");
  const result = await fetch(url);
  const response = await result.json();
  if (response.data) {
    const data = response.data;
    if (data.title) title.value = data.title;
    if (data.imprint) {
      // The ISTC data has an object for imprint
      const i = data.imprint[0];
      imprint.value = i.imprint_place + " " + i.imprint_name + " " + i.imprint_date;
    }
    if (data.author) author.value = data.author;
  }
}

function makeTrashButton(attrs, handler) {
  const t = document.createElement("div");
  t.style.display = "inline";
  t.style.marginRight = "2vw";
  t.style.cursor = "pointer";
  t.innerHTML = trash;
  for (const [name, value] of Object.entries(attrs)) {
    t.setAttribute(name, value);
  }
  t.addEventListener("click", handler);
  return t;
}

function removeVal(event) {
  const val = findAttrParents(event.target, "data-value");
  const field = findAttrParents(event.target, "data-field");
  const dest = findAttrParents(event.target, "data-dest");
  if (val && field) {
    document.obj[field] = (document.obj[field] || []).filter((x) => x != val);
  }
  setThe(field, dest, false, true);
  event.preventDefault();
}

function removeImage(event) {
  const toRemove = findAttrParents(event.target, "data-filename");
  if (toRemove) {
    document.obj.URL_IMAGE = (document.obj.URL_IMAGE || []).filter((x) => x != toRemove);
    showThumbnails();
  }
  event.preventDefault();
}

function showThumbnails() {
  const thumbs = document.getElementById("image_thumbnails");
  thumbs.innerHTML = "";
  for (const x of document.obj.URL_IMAGE || []) {
    const i = document.createElement("img");
    i.src = "/iiif/2/" + x + "/full/200,/0/default.jpg";
    i.style.marginRight = "4px";
    thumbs.appendChild(i);
    thumbs.appendChild(makeTrashButton({ "data-filename": x }, removeImage));
  }
}

function radioChoice(event) {
  const value = findAttrParents(event.target, "data-value");
  const dest = findAttrParents(event.target, "data-dest");
  const current = document.obj[dest] || [];

  if (event.target.checked) {
    if (!current.includes(value)) {
      current.push(value);
      document.obj[dest] = current;
    }
  } else if (current.includes(value)) {
    document.obj[dest] = current.filter((x) => x != value);
  }
}

async function filechosen(event) {
  // post the file to /api/upload
  // and set the returned hashfilename to the data here (if not already in the URL_IMAGE)
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
      const hashFilename = response.hash_filename;
      // Check if this returned hash is in the obj
      const urlImage = document.obj.URL_IMAGE || [];
      if (!urlImage.includes(hashFilename)) {
        urlImage.push(hashFilename);
        document.obj.URL_IMAGE = urlImage;
      }
      showThumbnails();
    } else {
      document.getElementById("image_thumbnails").innerHTML = response.detail;
    }
  } finally {
    fileuploadSpinner.style.display = "none";
  }
}

function modalClickHandler(event) {
  const field = event.target.getAttribute("data-field");
  const value = event.target.getAttribute("data-value");
  const target = event.target.getAttribute("data-target");
  if (field && value) {
    // Certain fields are multi
    if (["OWNERS_CERLID", "LOCATION_ORIG_CERLID", "IC"].includes(field)) {
      const current = document.obj[field] || [];
      if (!current.includes(value)) {
        current.push(value);
      }
      document.obj[field] = current;
      setThe(field, target, false, true);
    } else {
      document.obj[field] = [value];
      setThe(field, target, true);
    }
  }
}

function dropdownClickHandler(event) {
  let value = findAttrParents(event.target, "data-code");
  if (!value) {
    value = event.target.innerHTML;
  }
  const field = findAttrParents(event.target, "data-field");
  const target = findAttrParents(event.target, "data-target");

  if (field && value) {
    document.obj[field] = [value];
    if (field == "PAGE") {
      if (value == "Page/Folio number") {
        const elem = document.querySelector(target);
        elem.value = "";
        elem.focus();
      } else {
        setThe(field, target);
      }
    } else {
      setThe(field, target, true);
    }
    event.preventDefault();
  }
}

function modalSearchHandler(event) {
  event.preventDefault();
  document.ct_tipe = event.target.getAttribute("ct_tipe");
  document.ct_value = event.target.value;
  document.ct_target = event.target.getAttribute("ct_target");

  if (document.modal_search_bounce > 0) {
    clearTimeout(document.modal_search_bounce);
  }
  document.modal_search_bounce = setTimeout(doModalSearch, 750);
}

async function doModalSearch() {
  const result = await fetch(
    "/fragments/modal_search?q=" +
      encodeURI(document.ct_value) +
      "&tipe=" +
      encodeURI(document.ct_tipe)
  );
  const response = await result.text();
  document.getElementById(document.ct_target).innerHTML = response;
}

function setThe(field, dest, isModal = false, isMulti = false) {
  if (!(field in document.obj)) {
    return;
  }
  const elem = document.querySelector(dest);
  // special treatement for the url_seealso field
  if (field == "URL_SEEALSO") {
    if (document.obj[field]) {
      elem.innerHTML = document.obj[field].join("\n");
    }
    return;
  }
  if (isMulti) {
    elem.innerHTML = "";
  }
  for (const val of document.obj[field]) {
    let showval = val;
    if (field.endsWith("_CERLID")) {
      showval = val.split("|")[1];
    } else if (field == "LANG") {
      showval = LANGUAGES[val];
    }
    if (isModal) {
      elem.innerHTML = showval;
    } else if (isMulti) {
      const s = document.createElement("span");
      s.style.margin = "0 4px 0 0";
      s.innerHTML = showval;
      elem.appendChild(s);
      elem.appendChild(
        makeTrashButton(
          { "data-value": val, "data-field": field, "data-dest": dest },
          removeVal
        )
      );
    } else {
      elem.value = showval;
    }
  }
}

function fromThe(field, src) {
  const elem = document.querySelector(src);
  document.obj[field] = [elem.value];
}

function saveFields() {
  fromThe("URL_WEBPAGE", "#source_url");
  fromThe("COMMENT", "#notes");
  fromThe("CAPTION", "#caption");
  fromThe("TITLE", "#title");
  fromThe("PERSON_AUTHOR", "#author");
  fromThe("IMPRINT", "#imprint");
  fromThe("TEXT", "#transcription");
  fromThe("SHELFMARK", "#shelfmark");
  fromThe("DATE_ORIG", "#date");
  fromThe("WIDTH", "#width");
  fromThe("HEIGHT", "#height");
  fromThe("PAGE", "#page");
  const canyouhelp = document.querySelector("#canyouhelp");
  document.obj.CANYOUHELP = canyouhelp.checked ? [Date.now()] : [];
  // Handle the URL_SEEALSO field specially to only filter items that start with http
  document.obj.URL_SEEALSO = []; // default to empty, and only set if valid values
  const val = document.getElementById("url_seealso").value;
  if (val.length > 8) {
    const vals = val
      .split("\n")
      .filter((x) => x.startsWith("http://") || x.startsWith("https://"));
    if (vals.length > 0) {
      document.obj.URL_SEEALSO = vals;
    }
  }
}

async function savebuttonHandler(event) {
  event.preventDefault();

  saveFields();

  // clear all required fields first
  for (const afield of REQUIRED_FIELDS) {
    document.querySelector(FIELDS_MAP[afield]).style.border = "none";
  }

  const missingField = requiredFieldsFilled();
  if (missingField !== true) {
    const elem = document.querySelector(missingField);
    elem.style.border = "2px solid red";
    elem.focus();
    return;
  }

  const anid = document.obj.ID[0];
  const result = await fetch("/id/" + anid, {
    method: "PUT",
    credentials: "same-origin",
    headers: jsonHeaders,
    body: JSON.stringify(document.obj),
  });
  const response = await result.json();
  document.location = "/id/" + response.ID;
}

async function addMissingItem(event) {
  const data = {}; // "entry", "firstname", "nonsort", "addition"
  const missingTab = findAttrParents(event.target, "data-missing");
  if (missingTab == "place") {
    data.action = "add_place";
    const entry = document.getElementById("missing_place").value;
    if (entry.length < 2) {
      return;
    }
    data.entry = entry;
    const notes = document.getElementById("missing_place_comment").value;
    if (notes.length > 0) {
      data.notes = notes;
    }
  }
  if (missingTab == "person") {
    data.action = "add_person";
    const entry = document.getElementById("missing_lastname").value;
    if (entry.length < 2) {
      return;
    }
    data.entry = entry;
    for (const [elemName, keyName] of [
      ["missing_firstname", "firstname"],
      ["missing_prefix", "nonsort"],
      ["missing_owner_comment", "notes"],
    ]) {
      const tmp = document.getElementById(elemName).value;
      if (tmp.length > 1) {
        data[keyName] = tmp;
      }
    }
  }
  if (missingTab == "corporate") {
    data.action = "add_corporate";
    data.entry = document.getElementById("missing_corporatebody").value;
    data.notes = document.getElementById("missing_corporatebody_comment").value;
  }
  await fetch("/api/cerlthesaurus", {
    method: "POST",
    credentials: "same-origin",
    headers: jsonHeaders,
    body: JSON.stringify(data),
  });

  console.log("Added new " + missingTab);
}

async function init() {
  document.getElementById("source_url").addEventListener("keyup", sourceUrl);
  document.getElementById("filechooser").addEventListener("change", filechosen);

  for (const item of document.querySelectorAll(".add_missing_item")) {
    item.addEventListener("click", addMissingItem);
  }
  for (const item of document.querySelectorAll(".ct_modal_search")) {
    item.addEventListener("keyup", modalSearchHandler);
  }
  for (const item of document.querySelectorAll(".century_choice")) {
    item.addEventListener("change", radioChoice);
  }
  for (const item of document.querySelectorAll(".modal")) {
    item.addEventListener("click", modalClickHandler);
  }
  for (const item of document.querySelectorAll(".dropdown-item")) {
    item.addEventListener("click", dropdownClickHandler);
  }
  for (const button of document.querySelectorAll(".save_button")) {
    button.addEventListener("click", savebuttonHandler);
  }

  if (document.objId) {
    const result = await fetch("/id/" + document.objId + ".json");
    document.obj = await result.json();
    setThe("URL_WEBPAGE", "#source_url");
    setThe("COMMENT", "#notes");
    setThe("CAPTION", "#caption");
    setThe("TITLE", "#title");
    setThe("PERSON_AUTHOR", "#author");
    setThe("IMPRINT", "#imprint");
    setThe("TEXT", "#transcription");
    setThe("SHELFMARK", "#shelfmark");
    setThe("DATE_ORIG", "#date");
    setThe("WIDTH", "#width");
    setThe("HEIGHT", "#height");
    setThe("NOTES", "#notes");
    setThe("IC", "#iconclass", false, true);
    setThe("INSTIT_CERLID", "#institution", true);
    setThe("TYPE_INS", "#kindofprovenance", true);
    setThe("PAGE", "#page");
    setThe("LANG", "#language", true);
    setThe("TECHNIQUE", "#technique", true);
    setThe("OWNERS_CERLID", "#owners", false, true);
    setThe("LOCATION_ORIG_CERLID", "#places", false, true);
    setThe("URL_SEEALSO", "#url_seealso");
    showThumbnails();
  }
}

window.addEventListener("load", init);
