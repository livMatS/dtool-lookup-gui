# Configuration file for the Sphinx documentation builder.

# -- Prepare

import shutil
import os

root = os.path.dirname(__file__)

# Define the source and destination paths for images
data_source_dir = os.path.join(root, '..', '..', 'data')
data_destination_dir = os.path.join(root, 'data')

# Copy images from source to destination
shutil.rmtree(data_destination_dir, ignore_errors=True)  # Remove existing destination directory
shutil.copytree(data_source_dir, data_destination_dir)  # Copy images

# -- Project information

project = 'dtool-lookup-gui'
copyright = '2023, livMatS'
author = 'Antoine Sanner, Ashwin Vazhappilly, Johannes Laurin Hörmann, Lars Pastewka, Michal Rössler, Wolfram Nöhring'


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

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['data']
