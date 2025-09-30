'''
This module implements a class representing a pump.

'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing                 import Optional, Callable
import numpy                as np
from scipy.interpolate      import interp1d
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsm
import fluidsolve.comp_base as flsb
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity

# =============================================================================
# GLOBALS
# =============================================================================
N_CURVE_POINTS = 100

# =============================================================================
# PUMP CLASSES
# =============================================================================

#******************************************************************************
# Pump component
class Comp_Pump (flsb.Comp_Base):
  ''' Generic pump component. Subclassed for specific pumps (e.g. centrifugal).

  Args:
    vendor (str, optional): Vendor.
      Defaults to 'undefined'.
    spec (str, optional): Specifications.
      Defaults to 'undefined'.
    din (int | float | Quantity, optional): Pump inlet diameter (in mm).
      Defaults to 0 mm.
    dout (int | float | Quantity, optional): Pump outlet diameter (in mm).
      Defaults to 0 mm.
    speed0 (int | float | Quantity): Pump rated speed (in rpm).
    speed (int | float | Quantity, optional): Pump actual speed (in rpm).
      Defaults to speed0.
    hasdata (boolean, optional): If True, QH curve data has to be provided.
      Defaults to True
    dataQH (list, optional): The QH curve data as a list. The data in the list is like [Q0,H0, Q1, H1, ... Qn, Hn]
      Defaults to [].

  Returns:
    None
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'group' : 'Pump',
      'part'  : 'Generic',
      'sign'  : 1.0,
    })
    self._vendor: str = args_in.getArg(
      'vendor',
      [
          flsa.vFun.default('undefined'),
          flsa.vFun.istype(str),
      ]
    )
    self._spec: str = args_in.getArg(
      'spec',
      [
          flsa.vFun.default('undefined'),
          flsa.vFun.istype(str),
      ]
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
    self._speed0: str = args_in.getArg(
      'speed0',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.rpm),
      ]
    )
    self._speed: str = args_in.getArg(
      'speed',
      [
          flsa.vFun.default(self._speed0),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.rpm),
      ]
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
    hasdata: bool = args_in.getArg(
      'hasdata',
      [
          flsa.vFun.default(True),
          flsa.vFun.istype(bool),
      ]
    )
    dataQH: list = args_in.getArg(
      'dataQH',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    if hasdata:
      if len(dataQH) == 0:
        raise ValueError(f'No pump data (dataQH: {dataQH})')
      else:
        hdata = np.reshape(dataQH, (-1, 2))
        self._dataQ0 = hdata[:,0]
        self._dataH0 = hdata[:,1]
    super().__init__(**args_in.restArgs())
    self.updateCurve()

  def updateCurve(self) -> None:
    ''' Update the curve variables and functions.
    '''
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

  @property
  def vendor(self) -> str:
    ''' pump vendor

    Returns:
        str: the pump vendor.
    '''
    return self._vendor

  @property
  def spec(self) -> str:
    ''' pump specs (type number, ...)

    Returns:
        str: pump specs
    '''
    return self._spec

  @property
  def din(self) -> Quantity:
    ''' pump inlet diameter (in mm).

    Returns:
        Quantity: pump inlet diameter
    '''
    if self._din is None:
      return None
    else:
      return self._din.to(u.mm)

  @property
  def dout(self) -> Quantity:
    '''pump outlet diameter (in mm).

    Returns:
        Quantity: pump outlet diameter
    '''
    if self._dout is None:
      return None
    else:
      return self._dout.to(u.mm)

  @property
  def speed0(self) -> Quantity:
    ''' pump rated speed (in rpm)

    Returns:
        Quantity: pump rated speed
    '''
    return self._speed0

  @property
  def speed(self) -> int | float:
    ''' pump actual speed (in rpm)

    Returns:
        int | float: pump actual speed
    '''
    return self._speed

  @speed.setter
  def speed(self, value: int | float | Quantity) -> None:
    ''' set pump actual speed.

    Args:
        value (int | float | Quantity): actual speed (in rpm)
    '''
    self._speed = flsa.toUnits(value, u.rpm)
    self.updateCurve()

  @property
  def Qb(self) -> Quantity:
    ''' Minimum flowrate (in m3/h)

    Returns:
        Quantity: flow rate.
    '''
    return self._Qb

  @property
  def Qe(self) -> Quantity:
    ''' Maximimum flowrate (in m3/h)

    Returns:
        Quantity: flow rate.
    '''
    return self._Qe

  @property
  def Qc(self) -> Quantity:
    ''' Critical flowrate (in m3/h)

    Returns:
        Quantity: Critical flowrate
    '''
    return self._Qc

  @property
  def Hb(self) -> Quantity:
    ''' Minimum head (in m)

    Returns:
        Quantity: head.
    '''
    return self._Qb

  @property
  def He(self) -> Quantity:
    '''  Maximimum head (in m)

    Returns:
        Quantity: head.
    '''
    return self._Qe

  def calcH(self, Q: int | float | Quantity, use: int=1) -> Quantity:
    ''' Calculate head H in equivalent meter pipe.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    H = self._funQtoH(lQ.magnitude)
    if isinstance(H, np.ndarray):
      H[H <= 0] = 0
    else:
      H = max(0, H)
    return H * u.m

  def calcQ(self, H: int | float | Quantity, use: int=1) -> Quantity:
    ''' Calculate flow rate in m3/h.

    Args:
      H (int | float | Quantity): head (default in m).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

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

  def toString(self, detail=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    txt = super().toString(detail) + '\n' \
        + f'Pump: {self._vendor}: {self._spec}\n' \
        + f' Din:{self._din}, Dout:{self._dout}, speed0:{self._speed0}, speed:{self._speed}\n'
    return txt

#******************************************************************************
# Centrfugal Pump component
class Comp_PumpCentrifugal (Comp_Pump):
  ''' Centrifugal pump component.

  Args:
    impeller0 (int | float | Quantity): Pump rated impeller (in mm).
    impeller (int | float | Quantity, optional): Pump actual speimpellered (in mm).
      Defaults to impeller0.

  Returns:
    None
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'Centrifugal',
    })
    self._impeller0: str = args_in.getArg(
      'impeller0',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._impeller: str = args_in.getArg(
      'impeller',
      [
          flsa.vFun.default(self._impeller0),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    super().__init__(**args_in.restArgs())

  @property
  def impeller0(self) -> Quantity:
    ''' pump rated impeller size (in mm)

    Returns:
        Quantity: pump rated impeller size
    '''
    return self._impeller0

  @property
  def impeller(self) -> Quantity:
    ''' pump actual impeller size (in mm)

    Returns:
        Quantity: pump actual impeller size
    '''
    return self._impeller

  def updateCurve(self) -> None:
    ''' Update the curve variables and functions.
    '''
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
    self._Qb = self._dataQ0[0] * u.m**3/u.h
    self._Qe = self._dataQ0[-1] * u.m**3/u.h
    Qpts =  np.linspace(start=self._Qb.magnitude, stop=self._Qe.magnitude, num=N_CURVE_POINTS, endpoint=True)
    Hpts = self._funQtoH(Qpts)
    self._Qc = Qpts[np.argmax(Hpts)] * u.m**3/u.h

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    txt = f'Pump: {self._part} : {self._vendor}: {self._spec}\n' + \
          f' Din:{self._din}, Dout:{self._dout}, Impeller0:{self._impeller0}, Impeller:{self._impeller}, Speed0:{self._speed0}, Speed:{self._speed}\n'
    return txt

#******************************************************************************
# component for one or more pumps in serial
class Comp_PumpSerial (Comp_Pump):
  ''' Pump component representing a number of pumps in serial.

  Args:
    pumps (list): A list of pump components. This list must contain at least 1 pump.

  Returns:
    None
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'    : 'PumpSerial',
      'speed0'  : 1,
      'hasdata' : False,
    })
    self._pumps: str = args_in.getArg(
      'pumps',
      [
          flsa.vFun.istype(list),
          flsa.vFun.lenmin(1),
      ]
    )
    self._Qc      : Quantity  = None
    super().__init__(**args_in.restArgs())

  def updateCurve(self) -> None:
    ''' Update the curve variables and functions.
    '''
    for pump in self._pumps:
      if self._Qb is None or pump.Qb < self._Qb:
        self._Qb = pump._Qb
      if self._Qe is None or pump.Qe > self._Qe:
        self._Qe = pump._Qe
      if self._Qc is None or pump._Qc > self._Qc:
        self._Qc = pump._Qc
    self._dataQ =  np.linspace(start=self._Qb.magnitude, stop=self._Qe.magnitude, num=N_CURVE_POINTS, endpoint=True)
    self._dataH = sum([pump.calcH(Q=self._dataQ).magnitude for pump in self._pumps])
    self._funQtoH = interp1d(self._dataQ, self._dataH, fill_value='extrapolate')
    self._funHtoQ = interp1d(self._dataH, self._dataQ, fill_value='extrapolate')
    # curve critical point
    self._Qc = self._dataQ[np.argmax(self._dataH)] * u.m**3/u.h

  def calcH(self, Q: int | float | Quantity, use: int=1) -> Quantity:
    ''' Calculate head H in equivalent meter pipe.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return self._funQtoH(lQ.magnitude) * u.m

  def calcQ(self, H: int | float | Quantity) -> Quantity:
    ''' Calculate flow rate in m3/h.

    Args:
      H (int | float | Quantity): head (default in m).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Flow rate (in m3/h).
    '''
    lH = flsa.toUnits(H, u.m)
    return self._funHtoQ(lH.magnitude) * u.m**3/u.h

  def toString(self, detail=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = f'Serial pumps:'
    for pump in self._pumps:
      txt += f'  {pump.toString(sdetail)}'
    return txt

#******************************************************************************
# component for one or more pumps in parallel
class Comp_PumpParallel (Comp_Pump):
  ''' Pump component representing a number of pumps in parallel.

  Args:
    pumps (list): A list of pump components. This list must contain at least 1 pump.

  Returns:
    None
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'    : 'PumpSerial',
      'speed0'  : 1,
      'hasdata' : False,
    })
    self._pumps: str = args_in.getArg(
      'pumps',
      [
          flsa.vFun.istype(list),
          flsa.vFun.lenmin(1),
      ]
    )
    self._Qc      : Quantity  = None
    super().__init__(**args_in.restArgs())

  def updateCurve(self) -> None:
    ''' Update the curve variables and functions.
    '''
    Hmin = None
    Hmax = None
    for pump in self._pumps:
      if self._Qb is None or pump._Qb < self._Qb:
        self._Qb = pump._Qb
      if self._Qe is None or pump._Qe > self._Qe:
        self._Qe = pump._Qe
      if self._Qc is None or pump._Qc > self._Qc:
        self._Qc = pump._Qc
      Hma = max(pump.calcH(Q=pump._Qb), pump.calcH(Q=pump._Qc), pump.calcH(Q=pump._Qe))
      Hmi = min(pump.calcH(Q=pump._Qb), pump.calcH(Q=pump._Qc), pump.calcH(Q=pump._Qe))
      if Hmin is None or Hmi < Hmin:
        Hmin = Hmi
      if Hmax is None or Hma > Hmax:
        Hmax = Hma
    if Hmin<0*u.m:
      Hmin=0 *u.m
    #self._dataH0 =  np.linspace(start=0, stop=Hm.magnitude, num=100, endpoint=True)
    self._dataH0 =  np.linspace(start=Hmin.magnitude, stop=Hmax.magnitude, num=N_CURVE_POINTS, endpoint=True)
    self._dataQ0 = np.zeros(len(self._dataH0))
    for pump in self._pumps:
      hh = pump.calcQ(H=self._dataH0).magnitude
      self._dataQ0 += hh
    tr = np.argmax(self._dataQ0<=0)
    if tr>0:
      self._dataQ0 = self._dataQ0[:tr]
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

  def calcH(self, Q: int | float | Quantity, use: int=1) -> Quantity:
    ''' Calculate head H in equivalent meter pipe.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return self._funQtoH(lQ.magnitude) * u.m

  def calcQ(self, H: int | float | Quantity) -> Quantity:
    ''' Calculate flow rate in m3/h.

    Args:
      H (int | float | Quantity): head (default in m).
      use (int): direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Flow rate (in m3/h).
    '''
    lH = flsa.toUnits(H, u.m)
    return self._funHtoQ(lH.magnitude) * u.m**3/u.h

  def toString(self, detail=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = f'Parallel pumps:'
    for pump in self._pumps:
      txt += f'  {pump.toString(sdetail)}'
    return txt
