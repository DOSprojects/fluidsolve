'''
Hydraulic valve component models.

This module provides valve-related resistance components used to model
controllable pressure losses in hydraulic systems.

Main ideas:

* valves are modeled as resistance components,
* valve behavior is state-dependent (opening/position logic defined by each
  subclass),
* loss is evaluated through valve-specific coefficients and converted to head.

Design conventions:

* mounting direction is port 1 -> port 2,
* runtime flow direction is represented by ``sense``,
* valve classes inherit from ``Comp_Valve`` and specialize ``calcK`` and/or
  related helper methods,
* resulting head loss is returned through ``calcH`` in the same unit
  conventions as other components.

Typical extension pattern:

1. Subclass ``Comp_Valve``.
2. Define how ``state`` maps to hydraulic behavior.
3. Implement ``calcK`` (or equivalent) for that state.
4. Reuse the base ``calcH`` conversion pipeline.

Example::

  valve = Comp_Valve(D=50)
  valve.state = 1.0
  H = valve.calcH(2.0 * u.m**3 / u.h, sense=1)

Valve subclasses in this module are intended to be combined with pumps,
pipes, and fittings inside paths or full network solves.
'''
from typing import Any
# =============================================================================
# IMPORTS
# =============================================================================
import fluids.units as fu
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util      as flsu
import fluidsolve.medium    as flsme
import fluidsolve.comp_base as flsb
# units
u        = flsme.unitRegistry
Quantity = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# GENERIC VALVE
# =============================================================================
class Comp_Valve(flsb.Comp_Base):  # pylint: disable=invalid-name
  ''' Generic valve base class.

  State meaning is defined by subclasses.

  Args:
    D (int | float | Quantity, optional): Valve bore diameter (default in mm).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Resistance'
  _part   : str = 'Valve'
  _prefix : str = 'V'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    args_in = flsa.GetArgs(kwargs)
    self._D = args_in.getArg(
      'D',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.mm, need=False),
      ]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def state(self) -> float:
    ''' Valve state.

    Returns:
      int | float: State value.
    '''
    return self._state

  @state.setter
  def state(self, value: int | float) -> Any:
    ''' Set valve state.

    Args:
      value (int | float): State value.
    '''
    self._state = value

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout: int=2) -> float:  # pylint: disable=unused-argument
    '''
    Default valve behavior: open.
    '''
    return 0.0

  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> Quantity:
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.KtoH(self.calcK(lQ, sense, pin, pout), flsu.Qtov(lQ, self._D)) * self._sign

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def toString(self, detail: int=0) -> str:
    ''' Return string representation. '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    txt += f' State:{self._state:.2f} '
    txt += f' D:{self._D:.2f~P} '
    return txt

# =============================================================================
# NON-RETURN (CHECK) VALVE
# =============================================================================
class Comp_Valve_NR(Comp_Valve):  # pylint: disable=invalid-name
  '''
  Non-return (check) valve.

  Mounted flow direction:
    port 1 -> port 2 = allowed flow
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Valve_NR'

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> float:
    if (sense > 0 and pin < pout) or (sense < 0 and pin > pout):
      return 0.0
    else:
      return 1e6


# =============================================================================
# ON / OFF VALVE
# =============================================================================
class Comp_Valve_01(Comp_Valve):  # pylint: disable=invalid-name
  '''
  On/off valve.

  state:
    0.0 = closed
    1.0 = fully open
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Valve_01'

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> float:  # pylint: disable=unused-argument
    if self._state <= 0.0:
      return 1e6
    else:
      return 0.0

# =============================================================================
# THROTLING VALVE
# =============================================================================
class Comp_Valve_Kv(Comp_Valve):  # pylint: disable=invalid-name
  '''
  Throttling valve with equal percentage characteristic.

  state: valve position (0.0 = closed, 1.0 = fully open)
  Kv at position s = Kvs * (R^s - 1) / (R - 1)
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Valve_KV'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._Kvs = args_in.getArg(
      'Kvs',
      [flsa.vFun.istype(int, float)]
    )
    self._R = args_in.getArg(
      'R',
      [flsa.vFun.default(3.0),
       flsa.vFun.istype(int, float)]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def Kvs(self) -> float:
    ''' Fully-open flow coefficient Kvs.

    Returns:
      float: Kvs value (m³/h at 1 bar).
    '''
    return self._Kvs

  @Kvs.setter
  def Kvs(self, value: int | float) -> None:
    ''' Set fully-open flow coefficient.

    Args:
      value (int | float): Kvs value.
    '''
    self._Kvs = value

  @property
  def R(self) -> float:
    ''' Valve rangeability (authority ratio).

    Returns:
      float: R value (Kvs / Kvmin), default 3.0.
    '''
    return self._R

  @R.setter
  def R(self, value: int | float) -> None:
    ''' Set valve rangeability.

    Args:
      value (int | float): R value.
    '''
    self._R = value

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> float:  # pylint: disable=unused-argument
    state = min(max(0.0, self._state), 1.0)
    if state <= 0.0:
      return 1e6
    if self._R == 1.0:
      kv = self._Kvs * state
    else:
      kv = self._Kvs * (self._R ** state - 1.0) / (self._R - 1.0)
    return min(1e6, flsu.KvtoK(kv, self._D))

# =============================================================================
# 3-WAY VALVE
# =============================================================================
class Comp_Valve_3W(Comp_Valve):  # pylint: disable=invalid-name
  '''
  3-way valve.

  Ports:
    1 = common
    2 = branch A
    3 = branch B

  state:
    1 -> connect 1-2
    2 -> connect 1-3
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Valve_3W'
  _nports : int = 3
  _ports  : list = [[1,2], [1,3], [2,3]]
  _conn   : dict = {1: [[1,2]], 2: [[1,3]]}

  # --------------------------------------------------------------------------
  # PROPERTIES
  def connections(self, state: Any=None) -> Any:
    if state is None:
      state = self._state
    return [tuple(conn) for conn in self._conn.get(state, [])]

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> float:
    '''
    Fixed valve loss, independent of direction.
    '''
    k_values : dict = {
      1: {(1,2): 0.7},
      2: {(1,3): 0.7},
    }
    if self._state not in self._conn:
      raise ValueError(f'Invalid state for 3-way valve: {self._state}')
    if not (1 <= pin <= self._nports and 1 <= pout <= self._nports):
      raise ValueError(f'Invalid ports for 3-way valve: pin={pin}, pout={pout}')
    if pin == pout:
      raise ValueError(f'pin and pout must be different: pin={pin}, pout={pout}')
    k_state = k_values[self._state]
    if (pin, pout) in k_state:
      return k_state[(pin, pout)]
    elif (pout, pin) in k_state:
      return k_state[(pout, pin)]
    else:
      return 1e6

# =============================================================================
# DOUBLE SEAT VALVE
# =============================================================================
class Comp_Valve_DS(Comp_Valve):  # pylint: disable=invalid-name
  '''
  Double seat valve.

  Ports:
    state 1: 1-2 and 3-4 open
    state 2: 1-3 and 2-4 open
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Valve_DS'
  _nports : int = 4
  _ports  : list = [[1,2], [2,3], [3,4]]
  _conn   : dict = {1: [[1,2], [3,4]], 2: [[1,2], [2,3], [3,4]]}

  # --------------------------------------------------------------------------
  # PROPERTIES
  def connections(self, state: Any=None) -> Any:
    '''Return open port connections for the given valve state.

    Args:
      state (Any, optional): Valve state override. Uses current state when omitted.

    Returns:
      Any: List of open port-pair tuples.
    '''
    if state == 1:
      return [(1, 2), (3, 4)]
    elif state == 2:
      return [(1, 2), (1, 3), (3, 4)]
    else:
      return []

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int=1, pin: int=1, pout: int=2) -> float:
    ''' Fixed valve loss coefficient. '''
    k_values : dict = {
      1: {(1,2): 0.7, (3,4): 0.7},
      2: {(1,2): 0.7, (1,3): 0.7, (1,4): 0.7, (2,3): 0.7, (2,4): 0.7, (3,4): 0.7},
    }
    if self._state not in self._conn:
      raise ValueError(f'Invalid state for 3-way valve: {self._state}')
    if not (1 <= pin <= self._nports and 1 <= pout <= self._nports):
      raise ValueError(f'Invalid ports for 3-way valve: pin={pin}, pout={pout}')
    if pin == pout:
      raise ValueError(f'pin and pout must be different: pin={pin}, pout={pout}')
    k_state = k_values[self._state]
    if (pin, pout) in k_state:
      return k_state[(pin, pout)]
    elif (pout, pin) in k_state:
      return k_state[(pout, pin)]
    else:
      return 1e6
