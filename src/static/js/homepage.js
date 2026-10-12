import { findAttrParents } from "./shared.js";

const searchbox = document.getElementById("searchbox");
const searchresults = document.getElementById("searchresults");
const showrandom = document.getElementById("showrandom");

function doSearch() {
  document.location = "/search?q=" + searchbox.value;
}

function doSearchSuggest() {
  console.log(".");
}

function searchboxKeyup(event) {
  event.preventDefault();
  if (event.keyCode == 13) {
    doSearch();
  }

  if (document.searchbounce > 0) {
    clearTimeout(document.searchbounce);
  }
  document.searchbounce = setTimeout(doSearchSuggest, 500);
}

function resultHandler(event) {
  const anid = findAttrParents(event.target, "anid");
  if (anid) {
    event.preventDefault();
    document.location = "/id/" + anid;
  }
}

function setLocationToSearch(event) {
  event.preventDefault();
  document.location = "/search";
}

function init() {
  searchbox.addEventListener("keyup", searchboxKeyup);
  if (showrandom) {
    showrandom.addEventListener("click", setLocationToSearch);
  }
  searchresults.addEventListener("click", resultHandler);
  searchbox.focus();
}

window.addEventListener("load", init);
