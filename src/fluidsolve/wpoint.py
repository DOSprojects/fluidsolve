'''
This module implements some classes to represent a working point (in the Q-H plane).

One class is a static working point.
A second one contains a reference to a pump and a circuit.
This one can recalculate the Q and H depending on the changes in pump and circuit.
This one is needed to implement an interactive Q-H plot
'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing                 import Optional, Any
import numpy             as np
import fluids.units      as fu
from scipy.optimize         import fsolve
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util      as flsu
import fluidsolve.medium    as flsm
import fluidsolve.comp_base as flsb
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity


# =============================================================================
# WORKIN POINT CLASSES
# =============================================================================

#******************************************************************************
# (working) point in HQ plane
class Wpoint ():
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    self._name: str = args_in.getArg(
      'name',
      [
          flsa.vFun.default(''),
          flsa.vFun.istype((str)),
      ]
    )
    self._Q: Quantity = args_in.getArg(
      'Q',
      [
          flsa.vFun.default(0.0 * u.m**3/u.h),
          flsa.vFun.istype((int, float, Quantity)),
          flsa.vFun.tounits(u.m**3/u.h),
      ]
    )
    self._H: Quantity = args_in.getArg(
      'H',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype((int, float, Quantity)),
          flsa.vFun.tounits(u.m),
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

  @property
  def Q(self) -> Quantity:
    ''' Working point flow property.

    Returns:
      Quantity: Flow (in m3/h) property.
    '''
    return self._Q.to(u.m**3/u.h)

  @Q.setter
  def Q(self, value: int | float | Quantity) -> None:
    ''' Set flow property.

    Args:
      value (int | float | Quantity): Flow (default in m3/h).
    '''
    self._Q = flsa.toUnits(value, u.m**3/u.h)

  @property
  def H(self) -> Quantity:
    ''' Working point head property.

    Returns:
      Quantity: Head (in m) property.
    '''
    return self._H.to(u.m)

  @H.setter
  def H(self, value: int | float | Quantity) -> None:
    ''' Set head property.

    Args:
      value (int | float | Quantity): Head (default in m).
    '''
    self._H = flsa.toUnits(value, u.m)

  @property
  def Qmag(self) -> Quantity:
    ''' Working point flow magnitude property.

    Returns:
      Quantity: Flow magnitude property.
    '''
    return self._Q.to(u.m**3/u.h).magnitude

  @property
  def Hmag(self) -> Quantity:
    ''' Working point head magnitude property.

    Returns:
      Quantity: Head magnitude property.
    '''
    return self._H.to(u.m).magnitude

  def update(self) -> 'Wpoint':
    ''' Update the Q an H.
    In this base class, this does nothing an only returns itself.

    Returns:
      Wpoint: self.
    '''
    return self

  def __str__(self) -> str:
    if self._name=='':
      return f'Pt: Q: {self._Q.to(u.m**3/u.h):.2f~P}, H: {self.H.to(u.m):.2f~P}'
    else:
      return f'Pt {self._name}: Q: {self._Q.to(u.m**3/u.h):.2f~P}, H: {self.H.to(u.m):.2f~P}'

  def __repr__(self) -> str:
    if self._name=='':
      return f'Pt: Q: {self._Q.to(u.m**3/u.h):.2f~P}, H: {self.H.to(u.m):.2f~P}'
    else:
      return f'Pt {self._name}: Q: {self._Q.to(u.m**3/u.h):.2f~P}, H: {self.H.to(u.m):.2f~P}'

#******************************************************************************
# (working) point in HQ plane
class WpointDyn (Wpoint):
  def __init__(self, **kwargs: int) -> None:
    args_in: dict = flsa.GetArgs(kwargs)
    self._s1: Any = args_in.getArg(
      's1',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(flsb.Comp_Base),
      ]
    )
    self._s2: Any = args_in.getArg(
      's2',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(flsb.Comp_Base),
      ]
    )
    super().__init__(**args_in.restArgs())
    self.update()

  def update(self):
    ''' Update the Q an H.
    The recalculation is done on the data in pump and system.
    This can be useful if the data in system or pump is modified interactively.

    Returns:
      Wpoint: self.
    '''
    if self._s1 is not None and self._s2 is not None:
      self._Q, self._H= calcOperatingPoint(self._s1, self._s2)
    return self

# =============================================================================
# SOLVERS
# =============================================================================

#******************************************************************************
# Operating point
def calcOperatingPoint(c1: Any, c2:Any, guess=200) -> tuple:
  ''' Calculate an operating point for two given curves.
      Mostly this will be a pump curve and system curve.
      The component can be any component and thus be a series of components with Comp_Serial.

  Args:
      c1 (Comp_Base): The first component
      c2 (Comp_Base): The second component

  Returns:
      tuple: a tuple (Q, H)
  '''

  def F(Q: int | float):
    return (abs(c1.calcH(Q, 1)) - abs(c2.calcH(Q, 1))).magnitude

  res = fsolve(func=F, x0=guess)
  Q = res[0] * u.m**3/u.h
  H = abs(c2.calcH(Q, 1))
  return (Q, H)
