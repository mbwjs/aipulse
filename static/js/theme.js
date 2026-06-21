(function () {
  var stored = localStorage.getItem("theme");
  if (stored === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else if (stored === null && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();

document.addEventListener("DOMContentLoaded", function () {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;

  btn.addEventListener("click", function () {
    var html = document.documentElement;
    if (html.hasAttribute("data-theme")) {
      html.removeAttribute("data-theme");
      localStorage.setItem("theme", "light");
    } else {
      html.setAttribute("data-theme", "dark");
      localStorage.setItem("theme", "dark");
    }
  });
});
