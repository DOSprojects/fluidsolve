'''
This module implements basic medium properties.
It is based on the thermo module assosiated with fluids
https://thermo.readthedocs.io/thermo.chemical.html

'''
# =============================================================================
# IMPORTS
# =============================================================================
import fluids.units         as fu
from pint                   import _DEFAULT_REGISTRY as pint_u
from pint                   import Quantity as pint_q
from thermo.chemical        import Chemical
# module own
import fluidsolve.aux_tools as flsa
# =============================================================================
# units (to be used by other modules)
# =============================================================================
unitRegistry  = pint_u
u             = pint_u
Quantity      = pint_q

# =============================================================================
# SOME CONSTANTS
# =============================================================================
''' gravity '''
CTE_G     = 9.80665 * u.m/u.s**2
''' normal temperature '''
CTE_NT    = 20.0 * u.degC
''' normal pressure '''
CTE_NP    = (1.0 * u.atm).to(u.Pa)
''' the medium "water" at normal conditions '''
CTE_WATER = Chemical('water', P=CTE_NP.magnitude, T=CTE_NT.to(u.degK).magnitude)
''' density of water '''
CTE_RHO   = CTE_WATER.rho * u.kg/u.m**3
''' dynamic viscosity '''
CTE_MU    = CTE_WATER.mu  * u.Pa*u.s
''' kinematic viscosity '''
CTE_NU    = CTE_WATER.nu  * u.m**2/u.s
''' thermal conductivity of water '''
CTE_K     = CTE_WATER.k   * u.W/u.m/u.degK
''' absolute roughness (epsilon) of stainless steel '''
CTE_E_RVS = 1.6 * u.um

# =============================================================================
# MEDIUM CLASS
# =============================================================================
class Medium ():
  ''' Class represinting a medium.
      Can be created just using a name known to the fluids chemical module.
      Can also get an arbitrary name. In that case, the user has to provide the constants (rho, mu, ...)

  Args:
    prd (str, optional): The product (in the fluids chemical module) name.
      Defaults to 'water'.
    name (str, optional): Medium name.
      Defaults to self._prd.
    T (int | float | Quantity, optional): The temperature.
      Defaults to 20°C.
    p (int | float | Quantity, optional): The pressure.
      Defaults to atmospheric pressure.
    rho (int | float | Quantity, optional): The density.
      Defaults to water (at temperature).
    mu (int | float | Quantity, optional): The kinematic viscosity.
      Defaults to water (at temperature).
    k (int | float | Quantity, optional): The thermal conductivity.
      Defaults to water (at temperature).

  Returns:
    None
  '''
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
    # the product out of the chemical library, if it exists
    self._cprd = None
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
    # update the product with this conditions
    #self._updateProduct()
    # override rho, mu, k
    self._rho: Quantity = args.getArg(
      'rho',
      [
        flsa.vFun.default(CTE_RHO),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.kg/u.m**3)
      ]
    )
    self._mu: Quantity = args.getArg(
      'mu',
      [
        flsa.vFun.default(CTE_MU),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.Pa*u.s)
      ]
    )
    self._k: Quantity = args.getArg(
      'k',
      [
        flsa.vFun.default(CTE_K),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.W/u.m/u.degK)
      ]
    )

  @property
  def name(self) -> str:
    ''' Name property.

    Returns:
      Str: Name property.
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
  def T(self) -> Quantity:
    ''' Temperature property.

    Returns:
      Quantity: Temperature in °C (internally stored in K).
    '''
    return self._T.to(u.degC)

  @T.setter
  def T(self, value: int | float | Quantity) -> None:
    ''' Set temperature.

    Args:
      value (int | float | Quantity): temperature (default in °C).
    '''
    flsa.toUnits(value, u.degC)
    flsa.toUnits(value, u.degK)
    self._updateProduct()

  @property
  def p(self) -> Quantity:
    ''' Pressure property.

    Returns:
      Quantity: Pressure (in bar) property.
    '''
    return self._p

  @p.setter
  def p(self, value: int | float | Quantity) -> None:
    ''' Set pressure property.

    Args:
      value (int | float | Quantity): Presure (default in bar).
    '''
    flsa.toUnits(value, u.bar)
    self._updateProduct()

  @property
  def rho(self) -> Quantity:
    ''' Density property.

    Returns:
      Quantity: Density (in kg/m3) property.
    '''
    return self._rho

  @rho.setter
  def rho(self, value: int | float | Quantity) -> None:
    ''' Set density property.

    Args:
      value (int | float | Quantity): Density (default in kg/m3).
    '''
    flsa.toUnits(value, u.kg/u.m**3)

  @property
  def mu(self) -> Quantity:
    ''' Kinematic viscosity property.

    Returns:
      Quantity: kinematic viscosity (in Pa.s) property.
    '''
    return self._mu

  @mu.setter
  def mu(self, value: int | float | Quantity) -> None:
    ''' Set  kinematic viscosity property.

    Args:
      value (int | float | Quantity): Kinematic viscosity (default in Pa.s).
    '''
    flsa.toUnits(value, u.Pa*u.s)

  @property
  def k(self) -> Quantity:
    ''' Thermal conductivity property.

    Returns:
      Quantity: Thermal conductivity (in W/m/K) property.
    '''
    return self._k

  @k.setter
  def k(self, value: int | float | Quantity) -> None:
    ''' Set k property.

    Args:
      value (int | float | Quantity): Thermal conductivity (in W/m/K) property.
    '''
    flsa.toUnits(value, u.W/u.m/u.degK)

  def _updateProduct(self):
    ''' Update the properties from the chemical library product.
    '''
    if len(self._prd)>0:
      self._cprd = Chemical(self._prd, P=self._p.magnitude, T=self._T.to(u.degK).magnitude)
      self._rho  = self._cprd.rho * u.kg/u.m**3
      self._mu   = self._cprd.mu * u.Pa*u.s
      self._k    = self._cprd.k * u.W/u.m/u.degK
    else:
      self._cprd = None

  def __str__(self) -> str:
    ''' String representation

    Returns:
        str: String representation
    '''
    return self.toString(0)

  def toString(self, detail=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
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
    ''' Representation of the medium object

    Returns:
        str: representation
    '''
    if self._name=='':
      return f'Medium(prd="water",rho={self._rho:.2f~P}, mu={self._mu:.2e~P})'
    else:
      return f'Medium(name="{self._name}", prd="{self._prd}",rho={self._rho:.2f~P}, mu={self._mu:.2e~P})'
