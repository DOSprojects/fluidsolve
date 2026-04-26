'''
Pump component models and Q-H curve handling.

This module implements hydraulic pump components that act as energy sources
in the network solver. Pump behavior is primarily defined through Q-H curve
data and operating speed scaling.

Main features:

* generic pump base class with shared pump metadata,
* curve-driven head evaluation over flow,
* speed-dependent behavior through rated vs operating speed,
* support for catalogue-driven centrifugal pump definitions.

Design conventions:

* pumps add energy (``sign = +1``),
* mounting direction is port 1 -> port 2,
* flow direction is provided through ``sense``,
* ``sense = +1`` follows mounting direction,
* ``sense = -1`` represents reverse-flow use (no useful pump head),
* pump curves are interpreted as positive-head source data.

Implementation notes:

* curve interpolation is used to evaluate head at intermediate flow values,
* flow/head units are normalized with the shared unit registry,
* curve sampling helpers are available for plotting and working-point tools.

Typical usage::

  pump = Comp_PumpCentrifugal(
      dataQH=[0, 20, 10, 18, 20, 12],
      speed0=2900,
      speed=2600,
  )
  H = pump.calcH(8 * u.m**3 / u.h, sense=1)

These pump classes are typically instantiated via the core factory helpers,
which provide consistent naming and defaults across a full hydraulic model.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Callable, List, Any
import numpy as np
from scipy.interpolate import interp1d
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsme
import fluidsolve.comp_base as flsb
# units
u        = flsme.unitRegistry
Quantity = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# CONSTANTS
# =============================================================================
N_CURVE_POINTS = 100

# =============================================================================
# GENERIC PUMP
# =============================================================================
class Comp_Pump(flsb.Comp_Base):  # pylint: disable=invalid-name
  ''' Generic pump component class.

  Args:
    vendor (str, optional): Vendor name.
    spec (str, optional): Pump specification or type.
    din (int | float | Quantity, optional): Pump inlet diameter (mm).
    dout (int | float | Quantity, optional): Pump outlet diameter (mm).
    speed0 (int | float | Quantity): Pump rated speed (in rpm).
    speed (int | float | Quantity, optional): Pump operating speed (rpm).
    hasdata (bool, optional): Whether Q-H curve data is required.
    dataQH (list, optional): Q-H curve data as
      [Q0, H0, Q1, H1, ... , Qn, Hn].

  Returns:
    None
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Pump'
  _part   : str = 'Generic'
  _prefix : str = 'P'
  _sign   : float = +1.0

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._vendor = args_in.getArg(
      'vendor',
      [flsa.vFun.default('undefined'),
       flsa.vFun.istype(str)]
    )
    self._spec = args_in.getArg(
      'spec',
      [flsa.vFun.default('undefined'),
       flsa.vFun.istype(str)]
    )
    self._din: str = args_in.getArg(
      'din',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._dout: str = args_in.getArg(
      'dout',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._speed0 = args_in.getArg(
      'speed0',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.rpm)]
    )
    self._speed = args_in.getArg(
      'speed',
      [flsa.vFun.default(self._speed0),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.rpm)]
    )
    # curve
    self._Qb      : Quantity  = None
    self._Qe      : Quantity  = None
    self._Qc      : Quantity  = None
    self._Hb      : Quantity  = None
    self._He      : Quantity  = None
    self._dataQ0  : list      = None
    self._dataH0  : list      = None
    self._dataQ   : list      = None
    self._dataH   : list      = None
    self._funQtoH : Callable  = None
    self._funHtoQ : Callable  = None
    #
    hasdata = args_in.getArg(
      'hasdata',
      [flsa.vFun.default(True),
       flsa.vFun.istype(bool)]
    )
    dataQH = args_in.getArg(
      'dataQH',
      [flsa.vFun.default([]),
       flsa.vFun.istype(list)]
    )
    if hasdata:
      if not dataQH:
        raise ValueError(f'No pump data (dataQH: {dataQH})')
      arr = np.reshape(dataQH, (-1, 2))
      self._dataQ0 = arr[:, 0]
      self._dataH0 = arr[:, 1]
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    self.updateCurve()

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def vendor(self) -> str:
    ''' Pump vendor.

    Returns:
      str: Pump vendor.
    '''
    return self._vendor

  @property
  def spec(self) -> str:
    ''' Pump specification (for example model or type number).

    Returns:
      str: Pump specification.
    '''
    return self._spec

  @property
  def din(self) -> Quantity:
    ''' Pump inlet diameter (mm).

    Returns:
      Quantity: Pump inlet diameter.
    '''
    if self._din is None:
      return None
    else:
      return self._din.to(u.mm)

  @property
  def dout(self) -> Quantity:
    ''' Pump outlet diameter (mm).

    Returns:
      Quantity: Pump outlet diameter.
    '''
    if self._dout is None:
      return None
    else:
      return self._dout.to(u.mm)

  @property
  def speed0(self) -> Quantity:
    ''' Pump rated speed (rpm).

    Returns:
      Quantity: Pump rated speed.
    '''
    return self._speed0

  @property
  def speed(self) -> int | float:
    ''' Pump operating speed (rpm).

    Returns:
      int | float: Pump operating speed.
    '''
    return self._speed

  @speed.setter
  def speed(self, value: int | float | Quantity) -> None:
    ''' Set pump operating speed.

    Args:
      value (int | float | Quantity): Operating speed (rpm).
    '''
    self._speed = flsa.toUnits(value, u.rpm)
    self.updateCurve()

  @property
  def Qb(self) -> Quantity:
    ''' Minimum flow rate (m3/h).

    Returns:
      Quantity: Flow rate.
    '''
    return self._Qb

  @property
  def Qe(self) -> Quantity:
    ''' Maximum flow rate (m3/h).

    Returns:
      Quantity: Flow rate.
    '''
    return self._Qe

  @property
  def Qc(self) -> Quantity:
    ''' Critical flow rate (m3/h).

    Returns:
      Quantity: Critical flow rate.
    '''
    return self._Qc

  @property
  def Hb(self) -> Quantity:
    ''' Lower curve-bound marker.

    Returns:
      Quantity: Lower bound marker.
    '''
    return self._Hb

  @property
  def He(self) -> Quantity:
    ''' Upper curve-bound marker.

    Returns:
      Quantity: Upper bound marker.
    '''
    return self._He

  @property
  def dataH(self) -> list:
    ''' curve H data.

    Returns:
      list: curve H data.
    '''
    return self._dataH

  @property
  def dataQ(self) -> list:
    ''' curve Q data.

    Returns:
      list: curve Q data.
    '''
    return self._dataQ

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate pump head.
        Reverse flow produces no head.

    Args:
      Q (int | float | Quantity): Flow rate (default unit: m3/h).
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Pump head (m).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h).magnitude
    lsense = sense if pin < pout else -sense
    # Effective flow sign in the pump's own 1->2 mounting direction.
    flow_sign = np.sign(lQ) * lsense
    H = self._funQtoH(np.abs(lQ))
    #print(f'pump---{self._name}-------------------', lQ, sense, pin, pout, flow_sign, H)
    if isinstance(H, np.ndarray):
      H = np.asarray(H, dtype=float)
      H[flow_sign < 0] = 0
      H[H <= 0] = 0
    else:
      if flow_sign < 0:
        H = 0
      else:
        H = max(0, H)
    return H * u.m


  def calcQ(self, H: Quantity, guess: Any=200, sense: int=1, pin: int=1, pout:int=2) -> Quantity:  # pylint: disable=unused-argument
    ''' Calculate flow rate from head.

    Args:
      H (int | float | Quantity): Head (default unit: m).
      guess (Any): Unused in pump inverse curve lookup; kept for API compatibility.
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Flow rate (in m3/h).
    '''
    lH = flsa.toUnits(H, u.m)
    Q = self._funHtoQ(lH.magnitude)
    if isinstance(Q, np.ndarray):
      Q[Q <= 0] = 0
    else:
      Q = max(0, Q)
    return Q * u.m**3/u.h

  # --------------------------------------------------------------------------
  # UTILITIES
  def updateCurve(self) -> Any:
    ''' Update curve arrays and interpolation functions. '''
    self._dataQ = self._dataQ0
    self._dataH = self._dataH0
    # probably in future: interp1d obsolete
    self._funQtoH = interp1d(self._dataQ, self._dataH, fill_value='extrapolate')
    self._funHtoQ = interp1d(self._dataH, self._dataQ, fill_value='extrapolate')
    #self._coeffQtoH = np.polyfit(self._dataQ, self._dataH, 2)
    #self._coeffHtoQ = np.polyfit(self._dataH, self._dataQ, 2)
    # curve min and max points
    self._Qb = min(self._dataQ) * u.m**3/u.h
    self._Qc = self._Qb
    self._Qe = max(self._dataQ) * u.m**3/u.h
    self._Hb = min(self._dataH) * u.m
    self._He = max(self._dataH) * u.m

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def toString(self, detail: int=0) -> str:
    ''' Return string representation.

    Args:
      detail (int, optional): Detail level.

    Returns:
      str: String representation.
    '''
    txt = super().toString(detail) + '\n' \
        + f'Pump: {self._vendor}: {self._spec}\n' \
        + f' Din:{self._din}, Dout:{self._dout}, speed0:{self._speed0}, speed:{self._speed}\n'
    return txt

# =============================================================================
# CENTRIFUGAL PUMP
# =============================================================================
class Comp_PumpCentrifugal(Comp_Pump):  # pylint: disable=invalid-name
  ''' Centrifugal pump component.

  Args:
    impeller0 (int | float | Quantity): Pump rated impeller (in mm).
    impeller (int | float | Quantity, optional): Pump operating impeller diameter (mm).

  Returns:
    None
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'Centrifugal'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._impeller0 = args_in.getArg(
      'impeller0',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    self._impeller = args_in.getArg(
      'impeller',
      [flsa.vFun.default(self._impeller0),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def impeller0(self) -> Quantity:
    ''' Pump rated impeller size (mm).

    Returns:
      Quantity: Pump rated impeller size.
    '''
    return self._impeller0

  @property
  def impeller(self) -> Quantity:
    ''' Pump operating impeller size (mm).

    Returns:
      Quantity: Pump operating impeller size.
    '''
    return self._impeller

  # --------------------------------------------------------------------------
  # PHYSICS

  # --------------------------------------------------------------------------
  # UTILITIES
  def updateCurve(self) -> None:
    ''' Update curve arrays and interpolation functions. '''
    # impact of speed - impeller size
    if self._speed == self._speed0:
      self._dataQ = self._dataQ0
      self._dataH = self._dataH0
    else:
      factor = (self._speed / self._speed0 * self._impeller / self._impeller0).magnitude
      self._dataQ = self._dataQ0 * factor
      self._dataH = self._dataH0 * factor ** 2
    # cut negative H
    ptrim = np.argmax(self._dataH<=0)
    if ptrim>0:
      self._dataQ = self._dataQ[:ptrim]
      self._dataH = self._dataH[:ptrim]
    # probably in future: interp1d obsolete
    self._funQtoH = interp1d(self._dataQ, self._dataH, fill_value='extrapolate')
    self._funHtoQ = interp1d(self._dataH, self._dataQ, fill_value='extrapolate')
    # curve begin, end, critical point
    self._Qb = self._dataQ[0] * u.m**3/u.h
    self._Qe = self._dataQ[-1] * u.m**3/u.h
    Qpts =  np.linspace(start=self._Qb.magnitude, stop=self._Qe.magnitude, num=N_CURVE_POINTS, endpoint=True)
    Hpts = self._funQtoH(Qpts)
    self._Qc = Qpts[np.argmax(Hpts)] * u.m**3/u.h

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def toString(self, detail: int=0) -> str:
    ''' Return string representation.

    Args:
      detail (int, optional): Detail level.

    Returns:
      str: String representation.
    '''
    txt = f'Pump: {self._part} : {self._vendor}: {self._spec}\n' + \
          f' Din:{self._din}, Dout:{self._dout}, Impeller0:{self._impeller0}, Impeller:{self._impeller}, Speed0:{self._speed0}, Speed:{self._speed}\n'
    return txt

# =============================================================================
# SERIAL PUMPS
# =============================================================================
class Comp_PumpSerial(Comp_Pump):  # pylint: disable=invalid-name
  ''' Pumps connected in series.
  Heads add, flow is identical.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'PumpSerial'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'hasdata': False,
      'speed0': 1*u.rpm,
    })
    self._pumps: List[Comp_Pump] = args_in.getArg(
      'pumps',
      [flsa.vFun.istype(list),
       flsa.vFun.lenmin(1)]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate head for the serial pump assembly.

    Args:
      Q (int | float | Quantity): Flow rate (default unit: m3/h).
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Head (m).
    '''
    if (sense < 0 and pin < pout) or (sense > 0 and pin > pout):
      return 0.0 * u.m
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return self._funQtoH(lQ.magnitude) * u.m

  def calcQ(self, H: int | float | Quantity, guess: Any=200, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate flow rate for the serial pump assembly.

    Args:
      H (int | float | Quantity): Head (default unit: m).
      guess (Any): Unused; kept for API compatibility.
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Flow rate (in m3/h).
    '''
    lH = flsa.toUnits(H, u.m)
    return self._funHtoQ(lH.magnitude) * u.m**3/u.h

  # --------------------------------------------------------------------------
  # UTILITIES
  def updateCurve(self) -> Any:
    ''' Update curve arrays and interpolation functions. '''
    for pump in self._pumps:
      if self._Qb is None or pump.Qb < self._Qb:
        self._Qb = pump.Qb
      if self._Qe is None or pump.Qe > self._Qe:
        self._Qe = pump.Qe
      if self._Qc is None or pump.Qc > self._Qc:
        self._Qc = pump.Qc
    self._dataQ =  np.linspace(start=self._Qb.magnitude, stop=self._Qe.magnitude, num=N_CURVE_POINTS, endpoint=True)
    self._dataH = sum(pump.calcH(Q=self._dataQ).magnitude for pump in self._pumps)
    self._funQtoH = interp1d(self._dataQ, self._dataH, fill_value='extrapolate')
    self._funHtoQ = interp1d(self._dataH, self._dataQ, fill_value='extrapolate')
    # curve critical point
    self._Qc = self._dataQ[np.argmax(self._dataH)] * u.m**3/u.h

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def toString(self, detail: int=0) -> str:
    ''' Return string representation.

    Args:
      detail (int, optional): Detail level.

    Returns:
      str: String representation.
    '''
    sdetail = detail // 10
    txt = 'Serial pumps:'
    for pump in self._pumps:
      txt += f'  {pump.toString(sdetail)}'
    return txt

# =============================================================================
# PARALLEL PUMPS
# =============================================================================
class Comp_PumpParallel(Comp_Pump):  # pylint: disable=invalid-name
  ''' Pumps connected in parallel.
  Flows add, head is identical.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'PumpParallel'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'hasdata': False,
      'speed0': 1*u.rpm,
    })
    self._pumps: List[Comp_Pump] = args_in.getArg(
      'pumps',
      [flsa.vFun.istype(list),
       flsa.vFun.lenmin(1)]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate head for the parallel pump assembly.

    Args:
      Q (int | float | Quantity): Flow rate (default unit: m3/h).
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Head (m).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return self._funQtoH(lQ.magnitude) * u.m

  def calcQ(self, H: int | float | Quantity, guess: Any=200, sense: int=1, pin: int=1, pout:int=2) -> Quantity:  # pylint: disable=unused-argument
    ''' Calculate flow rate for the parallel pump assembly.

    Args:
      H (int | float | Quantity): Head (default unit: m).
      guess (Any): Unused; kept for API compatibility.
      sense (int): Flow direction indicator (+1 or -1).
      pin (int): Inlet port number.
      pout (int): Outlet port number.

    Returns:
      Quantity: Flow rate (in m3/h).
    '''
    lH = flsa.toUnits(H, u.m)
    return self._funHtoQ(lH.magnitude) * u.m**3/u.h

  # --------------------------------------------------------------------------
  # UTILITIES
  def updateCurve(self) -> None:
    ''' Update curve arrays and interpolation functions. '''
    Hmin = None
    Hmax = None
    for pump in self._pumps:
      if self._Qb is None or pump.Qb < self._Qb:
        self._Qb = pump.Qb
      if self._Qe is None or pump.Qe > self._Qe:
        self._Qe = pump.Qe
      if self._Qc is None or pump.Qc > self._Qc:
        self._Qc = pump.Qc
      Hma = max(pump.calcH(Q=pump.Qb), pump.calcH(Q=pump.Qc), pump.calcH(Q=pump.Qe))
      Hmi = min(pump.calcH(Q=pump.Qb), pump.calcH(Q=pump.Qc), pump.calcH(Q=pump.Qe))
      if Hmin is None or Hmi < Hmin:
        Hmin = Hmi
      if Hmax is None or Hma > Hmax:
        Hmax = Hma
    Hmin = max(Hmin, 0 * u.m)
    #self._dataH0 =  np.linspace(start=0, stop=Hm.magnitude, num=100, endpoint=True)
    self._dataH0 =  np.linspace(start=Hmin.magnitude, stop=Hmax.magnitude, num=N_CURVE_POINTS, endpoint=True)
    self._dataQ0 = np.zeros(len(self._dataH0))
    for pump in self._pumps:
      hh = pump.calcQ(H=self._dataH0).magnitude
      self._dataQ0 += hh
    tr = np.argmax(self._dataQ0<=0)
    if tr>0:
      self._dataQ0 = self._dataQ0[:tr]
      self._dataH0 = self._dataH0[:tr]
    #print('tr',Hmin, Hmax, tr, self._dataQ0, self._dataH0)
    #self._dataQ0 = sum([pump.calcQ(H=self._dataH0).magnitude for pump in self._pumps])
    #i = np.where(self._dataQ0>0.01)
    #self._dataH0 = self._dataH0[1:j]
    #self._dataQ0 = self._dataQ0[1:j]
    self._dataQ = self._dataQ0
    self._dataH = self._dataH0
    self._Qb = self._dataQ0[-1] * u.m**3/u.h
    self._Qe = self._dataQ0[0] * u.m**3/u.h
    self._funQtoH = interp1d(self._dataQ0, self._dataH0, fill_value='extrapolate')
    self._funHtoQ = interp1d(self._dataH0, self._dataQ0, fill_value='extrapolate')

  # --------------------------------------------------------------------------
  # REPRESENTATION
  def toString(self, detail: int=0) -> str:
    ''' Return string representation.

    Args:
      detail (int, optional): Detail level.

    Returns:
      str: String representation.
    '''
    sdetail = detail // 10
    txt = 'Parallel pumps:'
    for pump in self._pumps:
      txt += f'  {pump.toString(sdetail)}'
    return txt
