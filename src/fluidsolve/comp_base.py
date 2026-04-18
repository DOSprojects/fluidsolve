'''
Base classes and adapters for hydraulic components.

This module defines the foundational component API used across fluidsolve.
Most concrete hydraulic elements (resistances, pumps, valves, paths, etc.)
inherit from ``Comp_Base`` and specialize its physics methods.

Core responsibilities of ``Comp_Base``:

* standardized argument parsing and unit normalization,
* shared component metadata (name, group, part, ports, sign, state),
* default head/pressure/flow calculation interface,
* cloning and human-readable representation helpers.

Physics conventions:

* ``calcH(Q, sense, pin, pout)`` returns head change,
* ``calcP(...)`` derives pressure change from head and medium density,
* ``calcQ(H, ...)`` numerically inverts ``calcH`` with Newton-Raphson,
* ``sign`` convention: ``+1`` for sources (pump-like), ``-1`` for resistances.

Extension pattern:

1. Subclass ``Comp_Base``.
2. Override fixed class attributes (group/part/prefix/ports/sign).
3. Override ``calcH`` (and optional helpers such as ``calcK``).
4. Keep constructor validation via ``GetArgs`` + ``vFun`` for consistency.

Additional utility classes:

* ``Comp_Dummy``: placeholder/no-op component.
* ``Comp_Reverse``: adapter that reverses flow-direction use of a wrapped
  component while delegating the rest of its interface.

Example::

  class MyLoss(Comp_Base):
      _group = 'Resistance'
      _part = 'MyLoss'

      def calcH(self, Q, sense=1, pin=1, pout=2):
          return 0.5 * sense * u.m
'''
from typing import Any
# =============================================================================
# IMPORTS
# =============================================================================
import copy
from scipy.optimize import fsolve
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util       as flsu
import fluidsolve.medium     as flsme
# units
u        = flsme.unitRegistry
Quantity = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# SENTINEL OBJECTS
# =============================================================================
NO_DIAMETER = object()
NO_LENGTH   = object()
NO_MEDIUM   = object()

# =============================================================================
# BASE HYDRAULIC COMPONENT CLASS
# =============================================================================
class Comp_Base:
  ''' Base hydraulic component class used by specific component types.

  Args:
    name (str, optional): Component name.
    state (int, optional): Component state (for example valve position).
    medium (str | flsme.Medium, optional): Fluid medium.
    e (int | float | Quantity, optional): Absolute roughness.

  Returns:
    None
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Base'
  _part   : str = 'Base'
  _prefix : str = 'X'
  _nports : int = 2
  _ports  : list = [[1,2]]
  _conn   : dict = {1: [[1,2]]}
  _sign   : float = -1.0   # +1 pump, -1 resistance

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._name: str = args_in.getArg(
      'name',
      [
        flsa.vFun.default(''),
        flsa.vFun.istype(str),
      ]
    )
    self._state: int = args_in.getArg(
      'state',
      [
        flsa.vFun.default(0),
        flsa.vFun.istype(int, float),
      ]
    )
    self._medium: flsme.Medium = args_in.getArg(
      'medium',
      [
        flsa.vFun.default(flsme.Medium(prd='water')),
        flsa.vFun.istype(str, flsme.Medium),
        flsa.vFun.tolambda(lambda x: x if isinstance(x, flsme.Medium) else flsme.Medium(prd=x)),
      ]
    )
    self._e: Quantity = args_in.getArg(
      'e',
      [
        flsa.vFun.default(flsme.CTE_E_RVS),
        flsa.vFun.istype(int, float, Quantity),
        flsa.vFun.tounits(u.um),
      ]
    )
    args_in.isEmpty()

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def name(self) -> str:
    ''' Component name '''
    return self._name

  @property
  def group(self) -> str:
    ''' Component group '''
    return self._group

  @property
  def part(self) -> str:
    ''' Component part type '''
    return self._part

  @property
  def nports(self) -> int:
    ''' Number of ports '''
    return self._nports

  @property
  def ports(self) -> list:
    ''' Component ports '''
    return self._ports

  #def connections(self, state: int | None = None):
  #  ''' Return internal port connections for the given state.
  #      Default: simple 2-port component
  #  '''
  #  return [(1, 2)]

  @property
  def medium(self) -> flsme.Medium:
    ''' Medium property. '''
    return self._medium

  @medium.setter
  def medium(self, value: str | flsme.Medium) -> None:
    if isinstance(value, str):
      self._medium = flsme.Medium(prd=value)
    elif not isinstance(value, flsme.Medium):
      raise TypeError(f'Medium must be a string or an instance of Medium, got {type(value)}')
    self._medium = value

  @property
  def e(self) -> Quantity:
    ''' Absolute roughness property. '''
    return self._e

  @e.setter
  def e(self, value: int | float | Quantity) -> None:
    self._e = flsa.toUnits(value, u.um)

  @property
  def sign(self) -> float:
    '''
    Energy sign:
    +1 = pump / energy source
    -1 = resistance (bends, tubes)
    For static height this depends on direction (up = -1.0, down = +1.0).
    Therefore the sign is handled in the static head term and the
    component sign remains +1.0.
    '''
    return self._sign

  @property
  def state(self) -> int | float:
    ''' Component state (e.g. valve position) '''
    return self._state

  @state.setter
  def state(self, value: int | float) -> None:
    self._state = value

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    '''
    Calculate head change.

    Args:
      Q: Flow rate.
      sense: +1 if flow is from pin to pout, -1 for reverse flow.
      pin: Inlet port number.
      pout: Outlet port number.

    Returns:
      Quantity: Head change in meters.
    '''
    return 0.0 * u.m

  def calcP(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    '''
    Calculate pressure change.

    Returns:
      Quantity: Pressure change.
    '''
    return flsu.Htop(self.calcH(Q, sense, pin, pout), self._medium.rho)

  def calcQ(self, H: Quantity, guess: Any=200, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    '''
    Calculate flow rate for a given head.

    Args:
      H: Head.
      guess: Initial flow guess.
      sense: Flow direction.
      pin: Inlet port number.
      pout: Outlet port number.

    Returns:
      Quantity: Flow rate in m3/h.
    '''
    def F(q: Any) -> Any:
      return (H - abs(self.calcH(q * u.m**3 / u.h, sense, pin, pout))).magnitude

    H = flsa.toUnits(H, u.m)
    res = fsolve(F, x0=guess)
    return res[0] * u.m**3 / u.h

  # --------------------------------------------------------------------------
  # UTILITIES
  def clone(self) -> Any:
    ''' Return a deep copy of the component. '''
    return copy.deepcopy(self)

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def __str__(self) -> str:
    return self.toString()

  def toString(self, detail: int = 0) -> str:
    ''' Return a string representation. '''
    txt = (
      f'Component "{self._name}" '
      f'[{self._group}:{self._part}] '
      f'ports={self._nports}, '
      f'state={self._state}, '
      f'Sign={"+" if self._sign > 0 else "-"}, '
      f'{self._medium.toString(detail)}'
    )
    return txt

# =============================================================================
# DUMMY COMPONENT CLASS
# =============================================================================
class Comp_Dummy(Comp_Base):
  ''' Dummy / empty component. '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group : str = 'Resistance'
  _part  : str = 'Dummy'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    ''' Initialize without requiring additional data. '''
    # Bypass Comp_Base.__init__ completely
    self._state  = 0
    self._medium = None
    args_in = flsa.GetArgs(kwargs)
    super().__init__(**args_in.restArgs())

# =============================================================================
# WRAPPER CLASS TO REVERSE USE A DIRECTIONAL COMPONENT
# =============================================================================
class Comp_Reverse(Comp_Base):
  ''' Adapter that reverses flow direction of a wrapped component. '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Reverse'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    args_in = flsa.GetArgs(kwargs)
    self._rev = args_in.getArg(
      'reverse',
      [flsa.vFun.istype(Comp_Base)]
    )
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Any:
    if hasattr(self._rev, 'calcK'):
      return self._rev.calcK(Q, -sense, pin, pout)
    raise AttributeError(f'{type(self._rev).__name__} has no calcK')

  def calcH(self, Q: Any, sense: int=1, pin: int=1, pout:int=2) -> float:
    return self._rev.calcH(Q, -sense, pin, pout)

  # --------------------------------------------------------------------------
  # TRANSPARENT DELEGATION
  def __getattr__(self, name: Any) -> Any:
    ''' Delegate unknown attributes to the wrapped component. '''
    return getattr(self._rev, name)
