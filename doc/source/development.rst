***********
Development
***********

In order to be able to contribute to this package, one nneeds a development system.

Development setup
=================

See the *Step by step installation (virtual environment)* section in the readme.

* Clone the GitHub repository.
* Put that repository in the D:\fluidsolve map.
* Install fluidsolve in editable mode
    * in the terminal:

        .. code-block:: console

            D:
            cd \fluidsolve
            pip install -e .

   some remarks: this will give an error if git is not initialized. The doc make needs git to get the version.

Coding guidelines
=================

* Use Python 3
* Use Docstrings for classes, methods and functions

Conventions
-----------

* Classes are ``PascalCased``
* Attributes are ``camelCased``
* Methods are ``camelCased``
* Functions are ``camelCased``
* Local variables are ``lowercased``
* Use 2 spaces indentation:
* Triple single quotes `'''` for docstrings
* Single quotes `'` for string literals

Testing
-------

Little testing has been written.
However, tests are strongly encouraged for anything with non-trivial logic.

Gotchas
-------

* To Do.

Submitting a Change Request
===========================

* Change Requests are always welcome.
* Please add an entry to the `CHANGELOG_` in your CR.
* It helps a lot if the CR description provides some context on what you are trying to do and why you think it's a good idea.
* The smaller the CR, the more quickly it might be reviewed.
* Keep in mind this is a hobby project and there can be months with little or no time to spend on this.
* Help with coding is a more valuable option - this whole module is no rocket science.

Filing a bug
============

* Please describe what you saw, what you expected to see, and how the bug can be reproduced.
* If it comes with a test case, even better!
