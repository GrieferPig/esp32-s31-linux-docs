SPHINXBUILD ?= sphinx-build
BUILDDIR ?= build
SPHINXOPTS ?=

.PHONY: help html html-en html-zh_CN html-index linkcheck clean

help:
	@echo "make html       Build English, Simplified Chinese and the landing page"
	@echo "make linkcheck  Check links in both languages and the landing page"
	@echo "make clean      Remove generated documentation"

html: html-en html-zh_CN html-index

html-en:
	@$(SPHINXBUILD) -b html -c . -d "$(BUILDDIR)/doctrees/en" -D language=en $(SPHINXOPTS) $(O) en "$(BUILDDIR)/html/en"

html-zh_CN:
	@$(SPHINXBUILD) -b html -c . -d "$(BUILDDIR)/doctrees/zh_CN" -D language=zh_CN $(SPHINXOPTS) $(O) zh_CN "$(BUILDDIR)/html/zh_CN"

html-index:
	@$(SPHINXBUILD) -b html -c . -d "$(BUILDDIR)/doctrees/index" -D language=en $(SPHINXOPTS) $(O) . "$(BUILDDIR)/html"

linkcheck:
	@$(SPHINXBUILD) -b linkcheck -c . -d "$(BUILDDIR)/doctrees/linkcheck-en" -D language=en $(SPHINXOPTS) $(O) en "$(BUILDDIR)/linkcheck/en"
	@$(SPHINXBUILD) -b linkcheck -c . -d "$(BUILDDIR)/doctrees/linkcheck-zh_CN" -D language=zh_CN $(SPHINXOPTS) $(O) zh_CN "$(BUILDDIR)/linkcheck/zh_CN"
	@$(SPHINXBUILD) -b linkcheck -c . -d "$(BUILDDIR)/doctrees/linkcheck-index" -D language=en $(SPHINXOPTS) $(O) . "$(BUILDDIR)/linkcheck/index"

clean:
	@$(SPHINXBUILD) -M clean . "$(BUILDDIR)"
