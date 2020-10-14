THIS_FILE     := $(realpath $(firstword $(MAKEFILE_LIST)))
THIS_DIR      := $(dir $(THIS_FILE))
CORE_PKG_DIR  := $(dir $(THIS_DIR))/sweetpea_core
CORE_DOCS_DIR := $(THIS_DIR)/sweetpea_core
CORE_AUTODOCS := $(CORE_DOCS_DIR)/autodoc

.DEFAULT_GOAL: default
.PHONY: default doc core-doc

default: doc

# Generate documentation for the whole project.
doc: _build core-doc
	sphinx-build . _build
	touch _build/.nojekyll

# Generate documentation from docstrings for sweetpea_core.
core-doc:
	sphinx-apidoc -o $(CORE_AUTODOCS)/ $(CORE_PKG_DIR)/

# Clone the static site.
_build:
	git clone https://github.com/sweetpea-org/sweetpea-org.github.io.git _build
