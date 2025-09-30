******
Readme
******

Description
===========

This Python module is meant to facilitate the calculations of head losses in circuits an the selection of suitable pomps.
It is built on **Fluids** `https://pypi.org/project/fluids/ <https://pypi.org/project/fluids/>`__,
**Thermo** `https://pypi.org/project/thermo/ <https://pypi.org/project/thermo/>`__
and **Pint** `https://pypi.org/project/Pint/ <https://pypi.org/project/Pint/>`__.

Use Cases
=========

* easy calculation of head losses
* pump working point determination
* visualisation of pump and circuit curves and working point
* orifice dimensioning

.. figure:: https://github.com/DOSprojects/fluidsolve/raw/main/doc/source/_images/basic.png
    :width: 45%

    Calculations

.. figure:: https://github.com/DOSprojects/fluidsolve/raw/main/doc/source/_images/plotserial.png
    :width: 45%

    Interactive Plot


The Fluid Solve tool
====================

This is a tool of toolkit, not a user friendly appication to do headloss calculations.
Thus the calculations scripts need to be written in Python.
Although this is all relative simple code, some knowledge of python will be necessary.
We will use Python (at least version 3.10) with some additional libraries.
If you install it via ``pip`` (see below), these dependencies will be installed together with the tool, 

Usage
=====

This module contains a number of functionalities:

* Medium definition.
* Component definition.
* Pump definition.
* Circuit definition (consisting of one ore more components).
* Pump and component selection (from catalogue)
* Plotting (static or interactive) Q-H graphs.
* Orifice dimensioning.

Take a look at the included examples for more info.

**IMPORTANT NOTE:**

In order to reduce typing there is only one namespace: fluidsolve.
So when in the documentation there is: ``fluidsolve.extplot.QHcurve``, you have to type ``fluidsolve.QHcurve``. 
Or when you ``from fluidsolve import *``, you simply type ``QHcurve``.

Installation
============

fluidsolve is just a Python package, so:

    .. code-block:: console

        pip install fluidsolve

Step by step installation (basic)
=======================================

Two things are needed: a Python environment and an editor to create and run yous scripts.
For the python enviromnment, the most simple way is to download and install a Python interpreter.
As en editor one has a lot of options, but I would suggest something like Notepad++ or VSCode.

Every Python setup will do. But as an example the procedure below should work on windows.

* create on D: following map structure(this will be the loacation where you place your calculation scripts)

::

    D:\
    └── fluidsolve\

* Download a python interpreter from `https://www.python.org/downloads/windows/ <https://www.python.org/downloads/windows/>`__; choose Windows installer (64-bit)
* Double click to install; make sure to add the interpreter to path.
* Download Visual Studio Code (vscode) from `https://code.visualstudio.com/ <https://code.visualstudio.com/>`__; 
* Double click to install
* set the default terminal
    * Press Ctrl+Shift+P (or F1) to open the Command Palette.
    * To search for Terminal Settings type: *Terminal: Select Default Profile*
    * choose *command prompt*
* Install some vscode extensions:
    * Python
* Select Python default interpreter
    * Press Ctrl+Shift+P (or F1) to open the Command Palette.
    * To search for Terminal Settings type: *Python: select interpreter*
    * choose the interpreter
* To test the interpreter: open a terminal and type: *python --version*
* Install library (fluidsolve is just a Python package)
    * in the terminal:

    .. code-block:: console

        pip install fluidsolve

Step by step installation (virtual environment)
===============================================

When you already have a Python environment, or you want to separate this form other python environments, 
you have to add some steps in the procedure before, just before installing the fluidsolve library.
The complete procedure becomes (for details see above):

* create on D: following map structure

::

    D:\
    └── fluidsolve\
        └── ... (rest of the files)


* Download a python interpreter from `https://www.python.org/downloads/windows/ <https://www.python.org/downloads/windows/>`__; choose Windows installer (64-bit)
* Double click to install; make sure to add the interpreter to path.
* Download Visual Studio Code (vscode) from `https://code.visualstudio.com/ <https://code.visualstudio.com/>`__; 
* Double click to install
* set the default terminal
    * Press Ctrl+Shift+P (or F1) to open the Command Palette.
    * To search for Terminal Settings type: *Terminal: Select Default Profile*
    * choose *command prompt*
* Install some vscode extensions:
    * Python
    * Pylint
    * ...
* Setup a virtual environment
    * Open the Command Palette (Ctrl+Shift+P), search for **Python: Create Environment**
    * Select venv
    * Enter the python interpreter
    * After selecting the Python interpreter version, a notification will show the progress of the environment creation.
    * The environment folder (.venv) will appear in your workspace.
    * Open the Command Palette (Ctrl+Shift+P), search for **Python: Select Interpreter**
    * select the python interpreter from the venv
* To test the interpreter: open a terminal and type: *python --version*
* Install library (fluidsolve is just a Python package)
    * in the terminal:

    .. code-block:: console

        pip install fluidsolve

Support
=======

This library is under development.
So breaking changes are always possible.

fluidsolve works with Python 3.10 and higher.

Development setup
=================

See the development section.

Usage
=====

Take a look at the example scripts. 

Eventually activate the virtual environment: `d:\fluidsolve\_venv\fluidsolve\Scripts\activate`
You can check if it is activated with: `pip list`

References
==========

homepage : `https://github.com/DOSprojects/fluidsolve.git <https://github.com/DOSprojects/fluidsolve.git>`__

documentation : `https://fluidsolve.readthedocs.io/en/latest/index.html <https://fluidsolve.readthedocs.io/en/latest/index.html>`__