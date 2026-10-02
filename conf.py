from __future__ import annotations

import os
import re
from pathlib import Path

project = "ESP32-S31 Linux"
author = "ESP32-S31 Linux contributors"
copyright = "2026, ESP32-S31 Linux contributors"

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
    "sphinx_copybutton",
]
source_suffix = {".md": "markdown"}
root_doc = "index"
language = "en"
# Each language is a separate source directory. A build from the repository
# root contains only the language landing page.
exclude_patterns = ["build", "README.md", ".venv", "**/.git", "en", "zh_CN"]
templates_path = ["_templates"]
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": True,
    "navigation_depth": 5,
    "titles_only": False,
    "language_selector": True,
    "version_selector": False,
    "flyout_display": "hidden",
}
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3
myst_enable_extensions = ["colon_fence", "deflist", "fieldlist", "tasklist"]
myst_heading_anchors = 4

# These two landing-page links target sibling HTML builds, not source files.
linkcheck_ignore = [r"^(?:en|zh_CN)/index\.html$"]


def source_linkcheck_uri(app, uri):
    """Check each pinned source page once; keep line selections in the HTML."""
    # GitHub's line selections are client-side. Their ranges are checked
    # against the pinned source checkout during documentation review.
    if re.fullmatch(
        r"https://github\.com/[^/]+/[^/]+/blob/[0-9a-f]{40}/[^#]+#L\d+(?:-L\d+)?",
        uri,
    ):
        return uri.split("#", 1)[0]
    return None


def language_selector_data(app, pagename, templatename, context, doctree):
    """Supply local page URLs to the RTD theme's existing language selector."""
    if context.get("READTHEDOCS"):
        return
    landing = Path(app.srcdir) == Path(app.confdir)
    current = app.config.language
    projects = []
    for code, name in (("en", "English"), ("zh_CN", "简体中文")):
        page = "index" if landing else pagename
        if page not in {"search", "genindex"} and not (
            Path(app.confdir) / code / f"{page}.md"
        ).is_file():
            page = "index"
        target = f"{code}/{page}.html" if landing else f"../{code}/{page}.html"
        projects.append({
            "slug": code,
            "language": {"code": code.replace("_", "-"), "name": name},
            "urls": {"documentation": context["pathto"](target, resource=True)},
        })
    context["local_language_data"] = {"projects": {
        "current": next(project for project in projects if project["slug"] == current),
        "translations": [project for project in projects if project["slug"] != current],
    }}
    context["language_selector_label"] = "选择语言" if current == "zh_CN" else "Select language"


def setup(app):
    app.add_css_file("language-selector.css")
    if os.environ.get("READTHEDOCS") != "True":
        # Rendered by Sphinx from the theme's unmodified versions.js_t.
        app.add_js_file("js/versions.js")
        app.add_js_file("language-selector.js")
    app.connect("html-page-context", language_selector_data, priority=800)
    app.connect("linkcheck-process-uri", source_linkcheck_uri)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
