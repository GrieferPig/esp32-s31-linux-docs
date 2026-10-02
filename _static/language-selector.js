// Feed local translation URLs to sphinx_rtd_theme's own dropdown renderer.
// The theme owns the select element, current option, styling and change action.
document.addEventListener("DOMContentLoaded", () => {
  const element = document.getElementById("s31-language-data");
  if (!element) return;
  const data = JSON.parse(element.textContent);
  document.dispatchEvent(new CustomEvent("readthedocs-addons-data-ready", {
    detail: { data: () => data },
  }));
  const selector = document.querySelector(".language-switch select");
  if (selector) selector.setAttribute("aria-label", element.dataset.label);
});
