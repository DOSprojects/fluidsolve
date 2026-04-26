'''
Working-point models in the Q-H (flow-head) plane.

This module defines classes used to represent and update operating points of hydraulic systems, especially for pump/circuit analysis and plotting.

Main classes:

* ``Wpoint``: static working point storing fixed ``Q`` and ``H`` values.
* ``WpointDyn``: dynamic working point linked to pump/circuit behavior, recalculating operating conditions when upstream model parameters change.

Typical use cases:

* annotate operating points on Q-H diagrams,
* compute updated intersection points after speed or resistance changes,
* drive interactive plotting workflows where pump/circuit parameters vary.

Typical usage::

  wp = Wpoint(name='nominal', Q=5 * u.m**3 / u.h, H=12 * u.m)
  dyn = WpointDyn(name='op', pump=pump, circuit=circuit)
  dyn.recalc()
  print(dyn.Q, dyn.H)

'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
from typing                 import Any
import math
import warnings
from scipy.optimize         import root
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsm
import fluidsolve.comp_base as flsb
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity  # type: ignore[misc]


# =============================================================================
# WORKING POINT CLASSES
# =============================================================================

# =============================================================================
class Wpoint ():
  ''' Static working point in the Q-H plane.

  Args:
    name (str, optional): Working point label.
    Q (int | float | Quantity, optional): Flow rate (default in m3/h).
    H (int | float | Quantity, optional): Head (default in m).
  '''
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
    ''' Name of the working point. '''
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
    ''' Flow rate (in m3/h). '''
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
    ''' Head (in m). '''
    return self._H.to(u.m)

  @H.setter
  def H(self, value: int | float | Quantity) -> None:
    ''' Set head property.

    Args:
      value (int | float | Quantity): Head (default in m).
    '''
    self._H = flsa.toUnits(value, u.m)

  @property
  def Qmag(self) -> float:
    ''' Flow rate magnitude (in m3/h). '''
    return self._Q.to(u.m**3/u.h).magnitude

  @property
  def Hmag(self) -> float:
    ''' Head magnitude (in m). '''
    return self._H.to(u.m).magnitude

  def update(self) -> 'Wpoint':
    ''' Update Q and H. In this base class returns self unchanged.

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

# =============================================================================
class WpointDyn (Wpoint):
  ''' Dynamic working point that recalculates Q and H from two components.

  Args:
    s1 (Comp_Base, optional): First component (e.g. pump curve).
    s2 (Comp_Base, optional): Second component (e.g. system curve).
    guess (int | float | list, optional): Initial flow guess for the solver.
    name (str, optional): Working point label.
    Q (int | float | Quantity, optional): Initial flow rate (default in m3/h).
    H (int | float | Quantity, optional): Initial head (default in m).
  '''
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
    self._guess : int | float | list =args_in.getArg(
      'guess',
      [
          flsa.vFun.default(200),
          flsa.vFun.istype(int, float, list),
      ]
    )
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    self.update()

  def update(self) -> 'WpointDyn':
    ''' Recalculate Q and H from the two components.

    Returns:
      WpointDyn: self.
    '''
    if self._s1 is not None and self._s2 is not None:
      self._Q, self._H = calcOperatingPoint(self._s1, self._s2, self._guess)
    return self

# =============================================================================
# SOLVERS
# =============================================================================

# =============================================================================
def calcOperatingPoint(c1: Any, c2:Any, guess: Any=None) -> tuple:
  ''' Calculate the operating point for two intersecting curves.

  Typically a pump curve and a system curve; each component may itself
  be a composite (e.g. Comp_Serial).

  Args:
    c1 (Comp_Base): First component.
    c2 (Comp_Base): Second component.
    guess (int | float | list, optional): Initial flow guess for the solver.

  Returns:
    tuple[Quantity, Quantity]: Operating point (Q, H).
  '''

  def F(Q: int | float) -> Any:
    #return (abs(c1.calcH(Q, 1)) - abs(c2.calcH(Q, 1))).magnitude # this is not ok, you resume there is a sign change, we need to keep the sign to find the correct root
    return (c1.calcH(Q, 1) + c2.calcH(Q, 1)).magnitude

  if guess is None:
    x0_list = [0.5, 2.0, 10.0, 50.0, 200.0]
  elif isinstance(guess, (list, tuple)):
    x0_list = [float(item) for item in guess]
  else:
    x0_list = [float(guess)]
  last_msg = f'calcOperatingPoint({c1.name}, {c2.name}) did not converge.'
  methods = ('hybr', 'lm', 'df-sane')
  # Try each method for each initial guess until a finite solution is found.
  for x0 in x0_list:
    for method in methods:
      root_res = root(F, x0=x0, method=method)
      if not root_res.success:
        msg = str(root_res.message)
        last_msg = f'calcOperatingPoint({c1.name}, {c2.name}): {msg}' if msg else f'calcOperatingPoint({c1.name}, {c2.name}): root[{method}] failed with status={root_res.status}'
        continue
      q_mag = float(root_res.x.flat[0])
      if not math.isfinite(q_mag) or q_mag < 0.0:
        last_msg = f'calcOperatingPoint({c1.name}, {c2.name}): invalid root Q={q_mag}'
        continue
      break
    else:
      continue
    break
  else:
    warnings.warn(last_msg, RuntimeWarning, stacklevel=2)
    return (0.0 * u.m**3 / u.h, 0.0 * u.m)
  # process result
  Q = q_mag * u.m**3/u.h
  H = abs(c2.calcH(Q, 1))
  return (Q, H)
