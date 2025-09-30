# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.append(os.path.abspath("./_ext"))

# -- Project information -----------------------------------------------------
project = 'fluidsolve'
copyright = '2023, DOSprojects'
author = 'DOSprojects'
#release - import version from package
try:
  from fluidsolve.___version import __version__ as release
except ImportError:
  release = 'unknown'

# -- General configuration ---------------------------------------------------
# Add any Sphinx extension module names here, as strings.
# They can be extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
#    'sphinx_toolbox.more_autodoc.typehints',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]
# Extension settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_keyword = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_custom_sections = None
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = False
todo_include_todos = True

html_theme_options = {
    'navigation_depth': 4,
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
#language = 'python'

# List of patterns, relative to source directory, that match files and directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_gen']

#
keep_warnings = True

# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for a list of builtin themes.
#html_theme = 'nature'
html_theme = 'sphinx_rtd_theme'

# The name of the Pygments (syntax highlighting) style to use.
#pygments_style = # 'paraiso-dark' #'default', 'emacs', 'friendly', 'colorful', 'autumn', 'murphy', 'manni', 'material', 'monokai', 'perldoc', 'pastie', 'borland', 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode', 'igor', 'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu', 'arduino', 'rainbow_dash', 'abap', 'solarized-dark', 'solarized-light', 'sas', 'stata', 'stata-light', 'stata-dark', 'inkpot', 'zenburn', 'gruvbox-dark', 'gruvbox-light'

# Add any paths that contain custom static files (such as style sheets) here, relative to this directory.
# They are copied after the builtin static files, so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', '_images']

# -- Options for HTMLHelp output ---------------------------------------------
# Output file base name for HTML help builder.
#htmlhelp_basename = 'pyssian-doc'

# -- Extension configuration -------------------------------------------------
autosummary_generate = True

autodoc_default_options = {
    'members':           True,
    'undoc-members':     True,
    'show-inheritance':  True,
    'member-order':      'bysource',
    'ignore-module-all': True,
    'private-members':   True,
    'special-members':   '__init__, __str__, __repr__'
}
