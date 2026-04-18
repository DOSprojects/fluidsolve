'''
Material property definitions used by hydraulic components.

This module provides a lightweight ``Material`` model with the constants needed
for component calculations (for example density, thermal conductivity, and
surface roughness). It is designed to supply practical engineering defaults
while still allowing user overrides.

Main features:

* predefined defaults for common conditions,
* unit-aware material properties using the shared unit registry,
* simple initialization from a material key/name,
* explicit override of key properties for custom materials.

Typical use cases:

* define pipe/wall roughness assumptions,
* set density values for pressure/head related conversions,
* pass consistent material settings through factory-created components.

Typical usage::

  mat = Material(mat='rvs')
  custom = Material(name='custom_steel', rho=7800 * u.kg / u.m**3, e=5 * u.um)

The class intentionally keeps the data model compact so that materials remain
easy to construct, inspect, and serialize as part of larger hydraulic models.
'''
from typing import Any
# =============================================================================
# IMPORTS
# =============================================================================
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsme
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# SOME CONSTANTS
# =============================================================================
''' gravity '''
CTE_G     = 9.80665 * u.m/u.s**2
''' normal temperature '''
CTE_NT    = 20.0 * u.degC
''' density of water '''
CTE_RHO   = 1 * u.kg/u.m**3
''' thermal conductivity of water '''
CTE_K     = 1 * u.W/u.m/u.degK
''' absolute roughness (epsilon) of stainless steel '''
CTE_E_RVS = 1.6 * u.um

# =============================================================================
# MATERIAL CLASS
# =============================================================================
class Material ():
  ''' Class representing a material.
      Can be created just using a known name.
      Can also get an arbitrary name. In that case, the user has to provide the constants (rho, mu, ...)

  Args:
    mat (str, optional): The material (in the database) name.
      Defaults to 'rvs'.
    name (str, optional): Material name.
      Defaults to self._mat.
    T (int | float | Quantity, optional): The temperature.
      Defaults to 20°C.
    rho (int | float | Quantity, optional): The density.
      Defaults to water (at temperature).
    k (int | float | Quantity, optional): The thermal conductivity.
      Defaults to water (at temperature).
    e (int | float | Quantity, optional): The absolute roughness.
      Defaults to rvs.

  Returns:
    None
  '''
  def __init__(self, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._mat: str = args.getArg(
      'mat',
      [
          flsa.vFun.default('mat'),
          flsa.vFun.istype(str),
      ]
    )
    self._name: str = args.getArg(
      'name',
      [
          flsa.vFun.default(self._mat),
          flsa.vFun.istype(str),
      ]
    )
    # the product out of the material library, if it exists
    self._cmat = None
    # conditions
    self._T: Quantity = args.getArg(
      'T',
      [
        flsa.vFun.default(CTE_NT),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.degK)
      ]
    )
    # update the material with this conditions
    #self._updateProduct()
    # override rho, e
    self._rho: Quantity = args.getArg(
      'rho',
      [
        flsa.vFun.default(CTE_RHO),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.kg/u.m**3)
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
    self._e: Quantity = args.getArg(
      'e',
      [
        flsa.vFun.default(CTE_E_RVS),
        flsa.vFun.istype((float, Quantity)),
        flsa.vFun.tounits(u.um)
      ]
    )

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

  @property
  def e(self) -> Quantity:
    ''' Absolute roughness (epsilon) property.

    Returns:
      Quantity: absolute roughness (epsilon) (in um) property.
    '''
    return self._e

  @e.setter
  def e(self, value: int | float | Quantity) -> None:
    ''' Set e property.

    Args:
      value (int | float | Quantity): Absolute roughness (epsilon) (in um) property.
    '''
    flsa.toUnits(value, u.um)

  def _updateProduct(self) -> Any:
    ''' Update the properties from the material library.
    '''
    if len(self._prd)>0:
      self._cmat = None #Chemical(self._prd, P=self._p.magnitude, T=self._T.to(u.degK).magnitude)
      self._rho  = self._cmat.rho * u.kg/u.m**3
      self._k    = self._cmat.k * u.W/u.m/u.degK
      self._e    = self._cmat.k * u.um
    else:
      self._cmat = None

  def __str__(self) -> str:
    ''' String representation

    Returns:
        str: String representation
    '''
    return self.toString(0)

  def toString(self, detail: Any=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    if detail == 0:
      if self._name=='':
        return f'Material - : rho:{self._rho:.2f~P}, e:{self._e:.2e~P}'
      else:
        return f'Material {self._name}: rho:{self._rho:.2f~P}, e:{self._e:.2e~P}'
    else:
      if self._name=='':
        return f'Material - : T:{self._T:.2f~P}, rho:{self._rho:.2f~P}, e:{self._e:.2e~P}, k:{self._k:.2e~P}'
      else:
        return f'Material {self._name} : T:{self._T:.2f~P}, rho:{self._rho:.2f~P}, e:{self._e:.2e~P}, k:{self._k:.2e~P}'

  def __repr__(self) -> str:
    ''' Representation of the material object

    Returns:
        str: representation
    '''
    if self._name=='':
      return f'Material(mat="water",rho={self._rho:.2f~P}, e={self._e:.2e~P})'
    else:
      return f'Material(name="{self._name}", mat="{self._mat}",rho={self._rho:.2f~P}, mu={self._e:.2e~P})'
