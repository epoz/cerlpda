import "./scss/main.scss";
import { Dropdown, Popover } from "bootstrap";
import "@popperjs/core";
import imagesLoaded from "imagesloaded";
import Masonry from "masonry-layout";

document.imagesLoaded = imagesLoaded;

window.addEventListener("load", () => {
  let dropdownElementList = [].slice.call(
    document.querySelectorAll(".dropdown-toggle")
  );

  let dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
    let X = new Dropdown(dropdownToggleEl);
    return X;
  });

  let popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  let popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new Popover(popoverTriggerEl);
  });

  let overview = document.querySelector(".grid");
  let msnry;

  if (overview) {
    imagesLoaded(overview, () => {
      msnry = new Masonry(overview, {
        itemSelector: ".grid-item",
        columnWidth: ".grid-item",
        percentPosition: true,
      });
      msnry.layout();
      overview.masonry = msnry;
    });
  }
});
