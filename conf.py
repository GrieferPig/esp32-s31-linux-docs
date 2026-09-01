from __future__ import annotations

project = "ESP32-S31 Linux"
author = "ESP32-S31 Linux contributors"
copyright = "2026, ESP32-S31 Linux contributors"

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
    "sphinx_copybutton",
]
source_suffix = {".md": "markdown"}
master_doc = "index"
language = "en"
exclude_patterns = ["build", "README.md", ".venv", "**/.git"]
templates_path = ["_templates"]
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": False,
}
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3
myst_enable_extensions = ["colon_fence", "deflist", "fieldlist", "tasklist"]
myst_heading_anchors = 4
