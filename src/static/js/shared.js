// Walk up the DOM from element until an element with a non-empty attr is found
export function findAttrParents(element, attr) {
  const val = element.getAttribute(attr);
  if (val && val.length > 0) {
    return val;
  }
  const parent = element.parentElement;
  if (parent) {
    return findAttrParents(parent, attr);
  }
}
