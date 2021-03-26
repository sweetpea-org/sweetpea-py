# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC  ?= sphinx-apidoc
SOURCEDIR     = _source
APIDOCDIR     = $(SOURCEDIR)/_apidoc
BUILDDIR      = _build
MODULEDIR     = ../sweetpea

.PHONY: apidoc clean-apidoc help Makefile

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: apidoc
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Run SPHINXAPIDOC to automatically catalog all functionality in the sweetpea
# module, which will be used by SPHINXBUILD to generate documentation.
#
# This invocation uses the following options:
#   --module-first
#       In the generated documentation, put each module's own documentation
#       ahead of the documentation for its submodules.
#   --separate
#       Put module documentation on its own page.
#       TODO: Do I like this one?
#   --maxdepth 4
#       Limit the depth of each module's table of contents.
apidoc: apidoc-clean
	@$(SPHINXAPIDOC) --module-first --separate --maxdepth 4 \
	    --output-dir "$(APIDOCDIR)" "$(MODULEDIR)"

# Remove everything in the APIDOCDIR prior to generation.
apidoc-clean: Makefile
	@$(RM) "$(APIDOCDIR)"/*
