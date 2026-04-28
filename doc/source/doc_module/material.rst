The ``material`` submodule
==========================

This module defines the ``Material`` class and related constants used by
components that need wall/pipe material properties.

Overview
--------

The ``Material`` object is a lightweight, unit-aware container for:

* density ``rho``
* thermal conductivity ``k``
* absolute roughness ``e``
* reference temperature ``T``

By default, values are initialized from module constants and converted to the
internal unit system.

Public constants
----------------

The submodule exposes several constants:

* ``CTE_G``: gravitational acceleration
* ``CTE_NT``: normal/reference temperature
* ``CTE_RHO``: default density
* ``CTE_K``: default thermal conductivity
* ``CTE_E_RVS``: default absolute roughness (stainless steel)

It also exports:

* ``u``: shared unit registry
* ``Quantity``: quantity type alias

Usage examples
--------------

Create a material with defaults:

.. code-block:: python

   import fluidsolve as fls

   mat = fls.Material()
   print(mat)

Create a custom material with explicit values:

.. code-block:: python

   import fluidsolve as fls

   mat = fls.Material(
       mat='steel',
       name='Steel',
       T=30 * fls.u.degC,
       rho=800 * fls.u.kg / fls.u.m**3,
       k=2 * fls.u.W / fls.u.m / fls.u.degK,
       e=5 * fls.u.um,
   )

Notes
-----

* ``T`` is stored internally in Kelvin and exposed as degrees Celsius via the ``T`` property.
* Setters convert incoming numeric values to default units.
* ``_updateProduct()`` is currently a safe no-op placeholder for future
  material-library integration.

.. automodule:: fluidsolve.material
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: Quantity, u, unitRegistry