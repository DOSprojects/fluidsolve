'''
Fluid medium properties and shared unit infrastructure.

This module defines the unit registry used across fluidsolve and provides the
``Medium`` class, which encapsulates fluid-state properties required by
component and network calculations.

External dependencies:

* ``pint`` for unit-safe quantities,
* ``thermo`` for fluid property lookup from product names.

Main capabilities:

* expose shared unit aliases (``unitRegistry``, ``u``, ``Quantity``),
* define reference constants at normal conditions,
* create media from known thermo products,
* support user-defined media by overriding key properties (rho, mu, k).

Why this module is central:

Most hydraulic equations in the package convert between pressure, head,
velocity, and flow, all of which depend on medium properties and unit
consistency. This module provides that common foundation.

Typical usage::

  water = Medium(prd='water')
  custom = Medium(name='custom_mix', rho=950 * u.kg / u.m**3, mu=1.5e-3 * u.Pa * u.s)
  rho = water.rho

References:

* https://thermo.readthedocs.io/thermo.chemical.html
* https://pint.readthedocs.io/en/stable/
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Any
import fluids.units         as fu
from pint                   import _DEFAULT_REGISTRY as pint_u
from pint                   import Quantity as pint_q
from thermo.chemical        import Chemical
# module own
import fluidsolve.aux_tools as flsa
# =============================================================================
# UNITS (USED BY OTHER MODULES)
# =============================================================================
unitRegistry  = pint_u
u             = pint_u
Quantity      = pint_q  # type: ignore[misc]

# =============================================================================
# CONSTANTS
# =============================================================================
''' Gravitational acceleration. '''
CTE_G     = 9.80665 * u.m/u.s**2
''' Normal temperature. '''
CTE_NT    = 20.0 * u.degC
''' Normal pressure. '''
CTE_NP    = (1.0 * u.atm).to(u.Pa)
''' Water at normal conditions. '''
CTE_WATER = Chemical('water', P=CTE_NP.magnitude, T=CTE_NT.to(u.degK).magnitude)
''' Water density. '''
CTE_RHO   = CTE_WATER.rho * u.kg/u.m**3
''' Dynamic viscosity. '''
CTE_MU    = CTE_WATER.mu  * u.Pa*u.s
''' Kinematic viscosity. '''
CTE_NU    = CTE_WATER.nu  * u.m**2/u.s
''' Thermal conductivity of water. '''
CTE_K     = CTE_WATER.k   * u.W/u.m/u.degK
''' Absolute roughness (epsilon) of stainless steel. '''
CTE_E_RVS = 1.6 * u.um

# =============================================================================
# MEDIUM CLASS
# =============================================================================
class Medium ():
  ''' Class representing a medium.

      It can be created from a thermo product name.
      It can also be user-defined by explicitly providing properties
      such as rho, mu, and k.

  Args:
    prd (str, optional): Product name known to thermo.
    name (str, optional): Medium name.
    T (int | float | Quantity, optional): Temperature.
    p (int | float | Quantity, optional): Pressure.
    rho (int | float | Quantity, optional): Density.
    mu (int | float | Quantity, optional): Dynamic viscosity.
    k (int | float | Quantity, optional): Thermal conductivity.

  Returns:
    None
  '''
  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._prd: str = args.getArg(
      'prd',
      [
        flsa.vFun.default('water'),
        flsa.vFun.istype(str),
      ]
    )
    self._name: str = args.getArg(
      'name',
      [
        flsa.vFun.default(self._prd),
        flsa.vFun.istype(str),
      ]
    )
    # conditions
    self._T: Quantity = args.getArg(
      'T',
      [
        flsa.vFun.default(CTE_NT),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.degK)
      ]
    )
    self._p: Quantity = args.getArg(
      'p',
      [
        flsa.vFun.default(CTE_NP),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.bar)
      ]
    )
    # override rho, mu, k
    # update the product with this conditions
    self._rho_override = 'rho' in kwargs  # pylint: disable=invalid-name
    self._mu_override  = 'mu' in kwargs  # pylint: disable=invalid-name
    self._k_override   = 'k' in kwargs  # pylint: disable=invalid-name
    self._updateProduct()
    if (self._cprd is None and not (self._rho_override and self._mu_override and self._k_override)):
      raise ValueError('Medium must have a valid prd or have a rho, mu and k')
    if self._rho_override:
      self._rho: Quantity = args.getArg(
        'rho',
        [
          flsa.vFun.istype(float, Quantity),
          flsa.vFun.tounits(u.kg/u.m**3)
        ]
      )
    if self._mu_override:
      self._mu: Quantity = args.getArg(
        'mu',
        [
          flsa.vFun.istype(float, Quantity),
          flsa.vFun.tounits(u.Pa*u.s)
        ]
      )
    if self._k_override:
      self._k: Quantity = args.getArg(
        'k',
        [
          flsa.vFun.istype(float, Quantity),
          flsa.vFun.tounits(u.W/u.m/u.degK)
        ]
      )

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def name(self) -> str:
    ''' Name property.

    Returns:
      str: Name property.
    '''
    return self._name

  @name.setter
  def name(self, value: str) -> None:
    ''' Set name property.

    Args:
      value (str): Name.
    '''
    self._name = value
    self._updateProduct()

  @property
  def cprd(self) -> str:
    ''' underlying chemical object.

    Returns:
      Any: cprd property.
    '''
    return self._cprd

  @property
  def T(self) -> Quantity:
    ''' Temperature property.

    Returns:
      Quantity: Temperature in degC (internally stored in K).
    '''
    return self._T.to(u.degC)

  @T.setter
  def T(self, value: int | float | Quantity) -> None:
    ''' Set temperature.

    Args:
      value (int | float | Quantity): Temperature.
    '''
    self._T = flsa.toUnits(value, u.degK)
    self._updateProduct()

  @property
  def p(self) -> Quantity:
    ''' Pressure property.

    Returns:
      Quantity: Pressure property (bar).
    '''
    return self._p

  @p.setter
  def p(self, value: int | float | Quantity) -> None:
    ''' Set pressure property.

    Args:
      value (int | float | Quantity): Pressure.
    '''
    self._p = flsa.toUnits(value, u.bar)
    self._updateProduct()

  @property
  def rho(self) -> Quantity:
    ''' Density property.

    Returns:
      Quantity: Density property (kg/m3).
    '''
    return self._rho

  @rho.setter
  def rho(self, value: int | float | Quantity) -> None:
    ''' Set density property.

    Args:
      value (int | float | Quantity): Density (default in kg/m3).
    '''
    self._rho_override = True
    self._rho = flsa.toUnits(value, u.kg/u.m**3)

  @property
  def mu(self) -> Quantity:
    ''' Dynamic viscosity property.

    Returns:
      Quantity: Dynamic viscosity property (Pa.s).
    '''
    return self._mu

  @mu.setter
  def mu(self, value: int | float | Quantity) -> None:
    ''' Set dynamic viscosity property.

    Args:
      value (int | float | Quantity): Dynamic viscosity.
    '''
    self._mu_override = True
    self._mu = flsa.toUnits(value, u.Pa*u.s)

  @property
  def k(self) -> Quantity:
    ''' Thermal conductivity property.

    Returns:
      Quantity: Thermal conductivity property (W/m/K).
    '''
    return self._k

  @k.setter
  def k(self, value: int | float | Quantity) -> None:
    ''' Set thermal conductivity property.

    Args:
      value (int | float | Quantity): Thermal conductivity.
    '''
    self._k_override = True
    self._k = flsa.toUnits(value, u.W/u.m/u.degK)

  def _updateProduct(self) -> Any:
    ''' Update derived properties from the thermo product model. '''
    if len(self._prd)>0:
      self._cprd = Chemical(self._prd, P=self._p.to(u.Pa).magnitude, T=self._T.to(u.degK).magnitude)
      if not  self._rho_override:
        self._rho  = self._cprd.rho * u.kg/u.m**3
      if not  self._mu_override:
        self._mu   = self._cprd.mu * u.Pa*u.s
      if not  self._k_override:
        self._k    = self._cprd.k * u.W/u.m/u.degK
    else:
      self._cprd = None

  def __str__(self) -> str:
    ''' String representation.

    Returns:
      str: String representation.
    '''
    return self.toString(0)

  def toString(self, detail: int=0) -> str:
    ''' Return string representation.

    Args:
      detail (int, optional): Detail level.

    Returns:
      str: String representation.
    '''
    if detail == 0:
      if self._name=='':
        return f'Medium - : rho:{self._rho:.2f~P}, mu:{self._mu:.2e~P}'
      else:
        return f'Medium {self._name}: rho:{self._rho:.2f~P}, mu:{self._mu:.2e~P}'
    else:
      if self._name=='':
        return f'Medium - : T:{self._T:.2f~P}, p:{self._p:.2f~P}, rho:{self._rho:.2f~P}, mu:{self._mu:.2e~P}, k:{self._k:.2e~P}'
      else:
        return f'Medium {self._name} : T:{self._T:.2f~P}, p:{self._p:.2f~P}, rho:{self._rho:.2f~P}, mu:{self._mu:.2e~P}, k:{self._k:.2e~P}'

  def __repr__(self) -> str:
    ''' Representation of the medium object.

    Returns:
      str: Representation.
    '''
    if self._name=='':
      return f'Medium(prd="water",rho={self._rho:.2f~P}, mu={self._mu:.2e~P})'
    else:
      return f'Medium(name="{self._name}", prd="{self._prd}",rho={self._rho:.2f~P}, mu={self._mu:.2e~P})'
