# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also from the environment for the first two.
SPHINXOPTS    ?= -W
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Standaard HTML build met waarschuwingen als fouten
html:
    $(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)
    @echo "HTML generated in $(BUILDDIR)"
# HTML build zonder waarschuwingen als fouten
html-nowarn:
    $(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)
    @echo "HTML generated (no warnings as errors)"
# HTML build met verbose output
html-verbose:
    $(SPHINXBUILD) -b html -v $(SOURCEDIR) $(BUILDDIR)
    @echo "HTML generated in $(BUILDDIR) (verbose output)"
# Opruimen van gegenereerde bestanden
clean:
    rm -rf $(BUILDDIR)
    @echo "Build-directory $(BUILDDIR) cleaned"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
