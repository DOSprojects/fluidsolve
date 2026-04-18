***************
Release process
***************

Pro memory: creating a python package
-------------------------------------

Credits to `Publish Your Python Code to PyPI in 5 Simple Steps <https://builtin.com/data-science/how-to-publish-python-code-pypi>`_.
From this document one can find following workflow below.

    .. code-block:: console

        module
        ├── doc
        │   ├── build
        │   │   └── ...
        │   ├── source
        │   │   └── ...
        │   ├── genrst.bat
        │   ├── make.bat
        │   └── Makefile
        ├── src
        │   ├── fluidsolve
        │   │   ├── __init__.py
        │   │   ├── lib
        │   │   │   ├── cat... .json
        │   │   │   └── cat... .json
        │   │   └── ... .py
        │   ├── x_examples
        │   │   ├── __init__.py
        │   │   └── ... .py
        │   ├── x_tests
        │   │   ├── __init__.py
        │   │   └── ... .py
        │   ├── x_tools
        │   │   ├── __init__.py
        │   │   └── ... .py
        │   ├── ___version.py
        │   └── __init__.py
        ├── .gitattributes
        ├── .gitignore
        ├── .pylintrc
        ├── .pypirc
        ├── .readthedocs.yaml
        ├── CHANGELOG.rst
        ├── LICENSE
        ├── MANIFEST.in
        ├── pyproject.toml
        ├── requirements-dev.txt
        ├── requirements.txt
        └── usage.rst

Pre-release
^^^^^^^^^^^

* Fill in a new version number (e.g. ``X.Y.Z``) in ``src/fluidsolve/___version.py``
* Update `CHANGELOG.rst <../../CHANGELOG.rst>`_ with that number
* Update `pyproject.toml <../../pyproject.toml>`_ with that number

Make Package
^^^^^^^^^^^^

* commit all changes to git
* set the version as tag on this git-branch

  If this is omitted, then `setuptools_scm` creates some extended version number which causes to hang the upload to testpypi and pypi.

* Build it

      .. code-block:: console

         py -m build

* Check the build

      .. code-block:: console

         twine check dist/*

Check Package
^^^^^^^^^^^^^

* Create and activate a Virtual Environment. This isolates your test from the rest of your system.

      .. code-block:: console

         d:
         cd \fluidsolve\.venv
         python -m venv test_env  (answer yes on the vscode prompt) 
         d:\fluidsolve\.venv\test_env\Scripts\activate

* Install the Package Locally

      .. code-block:: console

         cd \fluidsolve
         pip install \fluidsolve\dist\fluidsolve-0.0.9-py3-none-any.whl

* Create a testscript `test.py`

      .. code-block:: console

         import fluidsolve as fls
         u = fls.unitRegistry
         Quantity = fls.Quantity
         Q = Quantity(1, u.m**3 / u.hr)
        
         flsbuilder = fls.ComponentBuilder()
         comp = flsbuilder.getComp(comp='Tube', L=100, D=50)
         print(f'H={comp.calcH(Q, 1):.2f~P} P={comp.calcP(Q, 1):.2f~P}')

* Test the Package

      .. code-block:: console

         python test.py


Releasing
^^^^^^^^^

* Head to `<https://github.com/DOSprojects/fluidsolve/releases/new>`_ and create the release there.
* Wait for GitHub Actions to complete the build and release.
* Confirm on `<https://pypi.org/project/fluidsolve/>`_ that the release made it there.

Follow-up
^^^^^^^^^

If all your files are ok, this command produces many lines of commands and ends with no error.
 
* Upload Package to TestPyPI:

    .. code-block:: console
 
        > py -m twine upload --verbose --repository testpypi --config-file .pypirc dist/* 

            INFO     Using configuration from E:\prj\dev_pc\fluidsolve\.pypirc
            Uploading distributions to https://test.pypi.org/legacy/
            INFO     dist\fluidsolve-0.5.0-py3-none-any.whl (143.7 KB)
            INFO     dist\fluidsolve-0.5.0.tar.gz (141.8 KB)
            INFO     username set by command options
            INFO     password set from config file
            INFO     username: __token__
            INFO     password: <hidden>
            Uploading fluidsolve-0.5.0-py3-none-any.whl
            100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 159.1/159.1 kB • 00:01 • 3.1 MB/s
            INFO     Response from https://test.pypi.org/legacy/:
                    200 OK
 
* Test Package on testPyPI:

    Create a new virtual environment

    Test to make sure the module works properly.

    .. code-block:: console
 
        > pip install --index-url https://test.pypi.org/simple/ fluidsolve

 
* Upload Package to PyPI:

    .. code-block:: console
 
        > python -m twine upload --repository PyPI dist/*
        If the package was already published and this is an update:

    .. code-block:: console
 
        > py -m twine upload --skip-existing --config-file .pypirc dist/*
 
* Test Package on PyPI
 
    Create a new virtual environment

    Test to make sure the module works properly.

    .. code-block:: console

        > pip install fluidsolve

Make Documentation
------------------

* Generate the documentation with Sphinx:

    .. code-block:: console
 
        > cd \fluidsolve\doc
        > make clean
        > make html

* check `.readthedocs.yaml` in the project root

* Push the Code to GitHub

  It is not needed to create a release.

* Connect to Read the Docs

    * Go to https://readthedocs.org
    * Sign in and connect to your GitHub account.
    * Search for the project (type some characters of fluidsolve and the project should be visible)
    * Import the project.

* Trigger a Build

    * Once imported, Read the Docs will automatically build your documentation.
    * The logs can be viewed.
    * Fix the issues if the build fails.