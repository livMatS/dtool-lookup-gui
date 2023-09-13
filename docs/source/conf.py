# Configuration file for the Sphinx documentation builder.
import os
import sys

root = os.path.dirname(sys.argv[0])

def read_authors(fn):
    return {email.strip('<>'): name for name, email in
            [line.rsplit(maxsplit=1) for line in open(fn, 'r')]}

authors = read_authors('{}/../../AUTHORS'.format(root))

authors_alphabetical = sorted(list(set(authors.values())))

# -- Project information

project = 'dtool-lookup-gui'
copyright = '2023, livMatS'
author = ', '.join(authors_alphabetical)

import dtool_lookup_gui
version = dtool_lookup_gui.__version__
release = dtool_lookup_gui.__version__

# release = '0.1'
# version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'myst_parser'
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
