# mmspy documentation build configuration file

import mmspy

# -- Project information -----------------------------------------------------
project = "mmspy"
copyright = "2024, Tien Vo"
author = "Tien Vo"
release = mmspy.__version__
version = mmspy.__version__[0]

# -- General configuration ---------------------------------------------------
source_suffix = ".rst"
root_doc = "index"
default_role = "py:obj"
pygments_style = "sphinx"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
]
templates_path = [
    "_templates",
]
exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
]

# -- Extension configurations ------------------------------------------------
# sphinx.ext.autodoc
autodoc_typehints = "none"

# sphinx.ext.extlinks
extlinks = {}

# sphinx.ext.intersphinx
intersphinx_mapping = {
    "attr": ("https://www.attrs.org/en/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "dask": ("https://docs.dask.org/en/latest", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "python": ("https://docs.python.org/3/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "zarr": ("https://zarr.readthedocs.io/en/latest/", None),
}

# sphinx.ext.napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_preprocess_types = True
napoleon_type_aliases = {
    # General
    "Sequence": "~collections.abc.Sequence",
    "Iterable": "~collections.abc.Iterable",
    "Callable": "~collections.abc.Callable",
    "string": ":class:`string <str>`",
    "Path": "~pathlib.Path",
    # numpy
    "array_like": ":term:`array_like`",
    "array-like": ":term:`array-like <array_like>`",
    "scalar": ":term:`scalar`",
    "array": ":term:`array`",
    "ndarray": "~numpy.ndarray",
    "dtype": "~numpy.dtype",
    # xarray
    "DataArray": "~xarray.DataArray",
    "Dataset": "~xarray.Dataset",
    # pandas
    "Timestamp": "~pandas.Timestamp",
    "Timedelta": "~pandas.Timedelta",
    "Index": "~pandas.Index",
    "NaT": "~pandas.NaT",
}

# sphinx.ext.todo
todo_include_todos = False

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_book_theme"
html_title = ""

html_theme_options = {
    "repository_url": "https://github.com/tien-vo/mmspy",
    "repository_branch": "main",
    "navigation_with_keys": False,
    "navigation_depth": 4,
    "path_to_docs": "docs",
    "use_edit_page_button": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "home_page_in_toc": True,
}

html_static_path = []
