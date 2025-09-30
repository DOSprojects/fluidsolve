'''
This module implements some classes that represent a hydraulic component.
Most of these classe inherit from a generic one.

#https://www.h2xengineering.com/blogs/hardy-cross-method-sizing-a-ring-main/
#https://www.colorado.edu/lab/krg/software-and-resources/tutorial-python-hardy-cross-method
'''
# =============================================================================
# IMPORTS
# =============================================================================
#from typing               import Optional, Any
import copy
from scipy.optimize         import fsolve
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util      as flsu
import fluidsolve.medium    as flsm
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity

# =============================================================================
# SENTINEL OBJECTS
# =============================================================================
NO_DIAMETER = object()
NO_LENGTH   = object()
NO_MEDIUM   = object()

# =============================================================================
# HYDRAULIC COMPONENT BASE CLASS
# =============================================================================
class Comp_Base ():
  ''' Base hydraulic component. Subclassed for specific components.

  Args:
    name (str, optional): Component name.
      Defaults to ''.
    group (str, optional): Group type.
      Defaults to 'Base'.
    part (str, optional): Part type.
      Defaults to 'Base'.
    sign (int | float): Indication if the component is a resistance (-1) or a 'pump' (+1).
      Defaults to -1.0.
    use (int | float): The direction in which the component is used: forward (+1.0) or backword (-1.0).
      Defaults to +1.0.
    medium (str | flsm.medium, optional): Fluid medium.
      Defaults to water.
    e (int | float | Guantity, optional): Tube roughness.
      Defaults to the RVS value (1.6um).

  Returns:
    None
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    self._name: str = args_in.getArg(
      'name',
      [
          flsa.vFun.default(''),
          flsa.vFun.istype(str),
      ]
    )
    self._group: str = args_in.getArg(
      'group',
      [
          flsa.vFun.default('Base'),
          flsa.vFun.istype(str),
      ]
    )
    self._part: str = args_in.getArg(
      'part',
      [
          flsa.vFun.default('Base'),
          flsa.vFun.istype(str),
      ]
    )
    self._sign: float = args_in.getArg(
      'sign',
      [
          flsa.vFun.default(-1.0),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(float),
      ]
    )
    self._use: float = args_in.getArg(
      'use',
      [
          flsa.vFun.default(+1.0),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(float),
      ]
    )
    self._medium: flsm.Medium = args_in.getArg(
      'medium',
      [
          flsa.vFun.default(flsm.Medium(prd='water')),
          flsa.vFun.istype(str, flsm.Medium),
          flsa.vFun.tolambda(lambda x: x if isinstance(x, flsm.Medium) else flsm.Medium(prd=x))
      ]
    )
    self._e: str = args_in.getArg(
      'e',
      [
          flsa.vFun.default(flsm.CTE_E_RVS),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.um),
      ]
    )
    args_in.isEmpty()

  @property
  def name(self) -> str:
    ''' Name property.

    Returns:
      str: Name property.
    '''
    return self._name

  @name.setter
  def name(self, value: str) -> None:
    ''' Name property.

    Args:
      value (str): Name.
    '''
    self._name = value

  @property
  def part(self) -> str:
    ''' Part type property.

    Returns:
      str: Part type.
    '''
    return self._part

  @property
  def sign(self) -> float:
    ''' This is an indication if this component adds energy to the system or if it is a 'resistor'.
        Pumps have a sign +1.0
        Appendages (bends, tubes) have a sign -1.0
        For static height, this depends: (up = -1.0, down = +1.0)
          therefore we leave the sign in the Hs property an give the component a sign +1.0

    Returns:
      float: sign.
    '''
    return self._sign

  @sign.setter
  def sign(self, value: int | float) -> None:
    ''' Set sign property.

    Args:
      value (int | float ): sign.
    '''
    self._sign = float(value)

  @property
  def use(self) -> float:
    ''' Direction in which the component is used.
        Some components behave the same no matter what direction the flow goes through the component (eg. a bend).
        For others this does has effect (eg. a reduction or diffusor, a static height going up or down)

    Returns:
      float: direction.
    '''
    return self._use

  @use.setter
  def use(self, value: int | float) -> None:
    ''' Set direction property.

    Args:
      value (int | float ): direction.
    '''
    self._use = float(value)

  @property
  def medium(self) -> flsm.Medium:
    return self._medium

  @medium.setter
  def medium(self, value: str | flsm.Medium) -> None:
    ''' Product name property.

    Args:
      value (str | flsm.Medium): Product name.
    '''

    if isinstance(value, str):
      self._medium = flsm.Medium(prd=value)
    elif not isinstance(value, flsm.Medium):
      raise TypeError(f'Medium must be a string or an instance of Medium, got {type(value)}')
    self._medium = value

  @property
  def e(self) -> Quantity:
    ''' Component absolute roughness property.

    Args:

    Returns:
      Quantity: Absolute roughness property
    '''
    return self._e

  @e.setter
  def e(self, value: int | float | Quantity) -> None:
    ''' Set absolute roughness property.

    Args:
      value (int | float | Quantity): Absolute roughness (default in um).
    '''
    self._e = flsa.toUnits(value, u.um)

  def clone(self):
    'Return a deep copy of this component.'
    return copy.deepcopy(self)

  def calcH(self, Q: int | float | Quantity, use: int=1) -> Quantity: # pylint: disable=unused-argument
    ''' Calculate head (loss) H in equivalent meter pipe.
        In case of head this will be a positive value, in case of head loss this will be a negative value.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): Direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    return 0.0 *u.m

  def calcP(self, Q: int | float | Quantity, use: int) -> Quantity: # pylint: disable=unused-argument
    ''' Calculate pressure loss P in bar.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): Direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Pressure loss P in bar.
    '''
    return flsu.Htop(self.calcH(Q, use), 1)

  def calcQ(self, H: int | float | Quantity, guess=200, use: int=1) -> Quantity:
    ''' Calculate flow rate for a given head.

    Args:
      H (int | float | Quantity): Head (default in m).
      guess (int | float): initial guess for solver.
      use (int): Direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Flow rate in m3/h.
    '''

    def F(Q: int | float):
      return (lH - abs(self.calcH(Q, use))).magnitude

    lH = flsa.toUnits(H, u.m)
    res = fsolve(func=F, x0=guess)
    Q = res[0] * u.m**3/u.h
    return Q


  def __str__(self) -> str:
    ''' String representation

    Returns:
        str: String representation
    '''
    return self.toString(0)

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    txt = f'Component "{self._name}" - {self._group}:{self._part} ' \
        + f'use:{"-" if self._use<0 else "+"} S:{"-" if self._sign<0 else "+"}, {self._medium.toString(detail)}'  # pylint: disable=inconsistent-quotes
    return txt
