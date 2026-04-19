'''
Hydraulic utility functions and conversion helpers.

This module contains standalone helpers used across fluidsolve for common
engineering calculations and unit-safe conversions. It is not centered on a
single class; instead, it provides reusable computational primitives.

Main responsibilities:

* pressure/head/velocity/flow conversion utilities,
* helper formulas for hydraulic loss calculations,
* convenience wrappers around selected ``fluids`` correlations,
* small numerical helper routines shared by components and tools.

Design intent:

* keep frequently reused equations in one importable location,
* avoid duplicating conversion logic in component classes,
* preserve unit consistency by using the shared quantity system.

Typical usage::

  H = PtoH(2.0 * u.bar, 998 * u.kg / u.m**3)
  P = Htop(10 * u.m, 998 * u.kg / u.m**3)
  out = calcOrifice(Q=2.5 * u.m**3 / u.h, d=50 * u.mm, orifice=20 * u.mm)

These helpers are intended as low-level building blocks used by higher-level
objects such as components, paths, and network solvers.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pyright: reportAttributeAccessIssue=false
# pylint: disable=no-member

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Any
import numpy                as np
import fluids.units         as fu
from scipy.optimize         import newton
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsme
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# SOME FUNCTIONS
# =============================================================================
def calcOrifice(**kwargs: Any) -> Any:
  ''' This function calculates either the flow rate, the upstream pressure,
      the second pressure or the orifice diameter for an orifice.

      For details see `https://fluids.readthedocs.io/fluids.flow_meter.html`

  Args:
      medium (Medium, optional): The medium to be used. Defaults to water
      Q (int | float | Quantity, optional): The flow rate.
        If not provided, this is the variable to be calculated.
      d (int | float | Quantity, optional): The pipe diameter (in mm)
        If not provided, this is the variable to be calculated.
      orifice (int | float | Quantity, optional): The orifice diameter size (in mm).
        If not provided, this is the variable to be calculated.
      Pin (int | float | Quantity, optional): The pressure before the orifice (in bar).
        If not provided, this is the variable to be calculated.
      Pout (int | float | Quantity, optional): The pressure after the orifice (in bar).
        If not provided, this is the variable to be calculated.
      meter (str, optional): Fluids orifice meter type.
      orifice (int | float | Quantity | str, optional): Orifice diameter (in mm) or, when used
        as the orifice_taps slot, the tap position string (e.g. ``'corner'``).
  '''

  args_in = flsa.GetArgs(kwargs)
  medium: flsme.Medium = args_in.getArg(
    'medium',
    [
        flsa.vFun.default(flsme.Medium(prd='water')),
        flsa.vFun.istype(str, flsme.Medium),
        flsa.vFun.tolambda(lambda x: x if isinstance(x, flsme.Medium) else flsme.Medium(prd=x))
    ]
  )
  m_in: int | float | Quantity = args_in.getArg(
    'Q',
    [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.m**3/u.h, need=False),
        flsa.vFun.tolambda(lambda x: x * medium.rho if x is not None else None)
    ]
  )
  d_in: int | float | Quantity = args_in.getArg(
    'd',
    [
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.mm, need=False),
    ]
  )
  d_orif: int | float | Quantity = args_in.getArg(
    'orifice',
    [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.mm, need=False),
    ]
  )
  P_in: int | float | Quantity = args_in.getArg(
    'Pin',
    [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.bar, need=False),
    ]
  )
  P_out: int | float | Quantity = args_in.getArg(
    'Pout',
    [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, Quantity, need=False),
        flsa.vFun.tounits(u.bar, need=False),
    ]
  )
  meter_type: str = args_in.getArg(
    'meter',
    [
        flsa.vFun.default('ISO 5167 orifice'),
        flsa.vFun.istype(str),
    ]
  )
  orifice_taps: str = args_in.getArg(
    'orifice',
    [
        flsa.vFun.default('corner'),
        flsa.vFun.istype(str),
    ]
  )
  args_in.isEmpty()
  calc_pars = flsa.prepareArgs(
    D = d_in,
    D2 = d_orif,
    P1 = P_in,
    P2 = P_out,
    m = m_in,
    rho = medium.rho,
    mu = medium.mu,
    k = medium.cprd.isentropic_exponent,
    meter_type = meter_type,
    taps = orifice_taps,
  )
  ans = fu.differential_pressure_meter_solver(**calc_pars)
  if d_in is None:
    return ans.to(u.mm)
  elif d_orif is None:
    return ans.to(u.mm)
  elif P_in is None:
    return ans.to(u.bar)
  elif P_out is None:
    return ans.to(u.bar)
  elif m_in is None:
    return (ans/medium.rho).to(u.m**3/u.h)
  else:
    return ans

def calcOrifice2(circuit: Any, Q: Any, d: Any, Puit: Any=1*u.bar, meter_type: Any='ISO 5167 orifice', orifice_taps: Any='corner') -> Any:
  ''' Solve for the orifice beta ratio that matches a given flow rate and circuit head.

  Args:
    circuit: Circuit object providing fluid properties and head curve.
    Q (Quantity): Flow rate.
    d (Quantity): Pipe diameter.
    Puit (Quantity, optional): Downstream pressure.
    meter_type (str, optional): Fluids orifice meter type.
    orifice_taps (str, optional): Fluids orifice taps.

  Returns:
    Quantity: Orifice diameter.
  '''

  def solverfun(beta: Any) -> Any:
    d_orif = d * beta
    # Solve naar upstream druk met gegeven flow en geschatte orifice diameter
    Pcalc = fu.differential_pressure_meter_solver(D=d, D2=d_orif, P2=Puit, m=m,
                                                  rho=circuit.rho, mu=circuit.mu, k=circuit.k, meter_type=meter_type, taps=orifice_taps)
    # Coefficient of discharge: Cd is karakteristiek orifice; bepaalt flow drukverlies bij nozzle en orifice
    C, _expansibility = fu.differential_pressure_meter_C_epsilon(D=d, D2=d_orif, m=m, P1=Pcalc, P2=Puit,
                                                                rho=circuit.rho, mu=circuit.mu, k=circuit.k, meter_type=meter_type, taps=orifice_taps)
    # Bereken dP voor geschatte orifice diameter
    dPcalc = fu.dP_orifice(D=d, Do=d_orif, P1=Pcalc, P2=Puit, C=C)
    err = dPcalc - dP
    print(f'Pcalc={Pcalc:.2f}, dPcalc={dPcalc:.4f}, err={err:.4f}, beta={beta:.4f}, C={C:.2f}')
    return err

  m = Q * circuit.rho
  H = circuit.calcH(Q)
  dP = fu.P_from_head(head=H, rho=circuit.rho)
  #Pin = Puit + dP                                 # druk boven = druk onder + drukverlies
  beta = newton(solverfun, x0=0.05, tol=1E-8)
  print(f'Orifice diameter: {d*beta}')
  return d*beta

# =============================================================================
def KtoFd(K: int | float, L: int | float | Quantity, D: int | float | Quantity) -> float:
  ''' Calculate friction factor Fd from loss coefficient K

  Args:
      K (int | float): loss coefficient
      L (int | float | Quantity): Length (default in m)
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      float: friction factor
  '''
  return (K * flsa.toUnits(D, u.mm) / flsa.toUnits(L, u.m)).magnitude

# =============================================================================
def FdtoK(Fd: int | float, L: int | float | Quantity, D: int | float | Quantity) -> float:
  ''' Calculate loss coefficient K from friction factor Fd

  Args:
      Fd (int | float): friction factor
      L (int | float | Quantity): Length (default in m)
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      float: loss coefficient
  '''
  return (Fd * flsa.toUnits(L, u.m) / flsa.toUnits(D, u.mm)).magnitude

# =============================================================================
def KvtoK(Kv: int | float | Quantity, D: int | float | Quantity) -> float:
  ''' Calculate loss coefficient K from valve flow coefficient Kv

  Args:
      Kv (int | float| Quantity): valve flow coefficient (default in m3/h)
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      float: loss coefficient
  '''
  lKv = flsa.toUnits(Kv, u.m**3/u.h)
  lD = flsa.toUnits(D, u.m)
  return (1.6E9 * (lD ** 4) * lKv **-2).magnitude

# =============================================================================
def KtoKv(K: int | float, D: int | float | Quantity) -> Quantity:
  ''' Calculate valve flow coefficient Kv from loss coefficient K

  Args:
      K (int | float): loss coefficient
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      Quantity: valve flow coefficient (in m3/h)
  '''
  lD = flsa.toUnits(D, u.m)
  return (4.E4 * ((lD ** 4 / K)**0.5)).to(u.m**3/u.h)

# =============================================================================
def CvtoK(Cv: int | float | Quantity, D: int | float | Quantity) -> float:
  ''' Calculate loss coefficient K from imperial valve flow coefficient Cv

  Args:
      Cv (int | float| Quantity): imperial valve flow coefficient (default in gallons/min)
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      float: loss coefficient
  '''
  lCv = flsa.toUnits(Cv, u.gal/u.min)
  lD = flsa.toUnits(D, u.m)
  return (1.6E9 * (lD ** 4) * (lCv / 1.156) **-2).magnitude

# =============================================================================
def KtoCv(K: int | float, D: int | float | Quantity) -> Quantity:
  ''' Calculate imperial valve flow coefficient Kv from loss coefficient K

  Args:
      K (int | float): loss coefficient
      D (int | float | Quantity): (Hydraulic) Diameter (default in mm)

  Returns:
      Quantity: valve flow coefficient (in gallons/min)
  '''
  lD = flsa.toUnits(D, u.m)
  return (1.156E4 * ((lD ** 4 / K)**0.5)).to(u.gal/u.min)

# =============================================================================
def CvtoKv(Cv: int | float | Quantity) -> float:
  ''' Calculate valve flow coefficient Kv from imperial valve flow coefficient Cv

  Args:
      Cv (int | float| Quantity): imperial valve flow coefficient (default in gallons/min)

  Returns:
      Quantity: valve flow coefficient (in m3/h)
  '''
  return (flsa.toUnits(Cv, u.gal/u.min)/ 1.156).to(u.m**3/u.h)

# =============================================================================
def KvtoCv(Kv: int | float | Quantity) -> float:
  ''' Calculate imperial valve flow coefficient Cv from valve flow coefficient Kv

  Args:
    Kv (int | float | Quantity): valve flow coefficient (default in m3/h)

  Returns:
    Quantity: imperial valve flow coefficient (in gallons/min)
  '''
  return (1.156 * flsa.toUnits(Kv, u.gal/u.min)).to(u.gal/u.min)

# =============================================================================
def KtoH(K: int | float, v: int | float | Quantity) -> Quantity:
  ''' Calculate hydraulic height from loss coefficient K

  Args:
      K (int | float): loss coefficient
      v (int | float | Quantity): fluid velocity (default in m/s)

  Returns:
      Quantity: hydraulic heigh (in m)
  '''
  lv = flsa.toUnits(v, u.m/u.s)
  return (K * 0.5 * lv * lv / flsme.CTE_G).to(u.m)

# =============================================================================
def Ktop(K: int | float, v: int | float | Quantity, rho: int | float | Quantity) -> Quantity:
  ''' Calculate hydraulic pressure from loss coefficient K

  Args:
      K (int | float): loss coefficient
      v (int | float | Quantity): fluid velocity (default in m/s)
      rho (int | float | Quantity): density (default in kg/m3)

  Returns:
      Quantity: hydraulic pressure (in bar)
  '''
  lv = flsa.toUnits(v, u.m/u.s)
  return (K * 0.5 * lv * lv * flsa.toUnits(rho, u.kg/u.m**3)).to(u.bar)

# =============================================================================
def Htop(H: int | float | Quantity, rho: int | float | Quantity) -> Quantity:
  ''' Calculate hydraulic pressure from hydraulic height

  Args:
      H (int | float | Quantity): hydraulic height (default in m)
      rho (int | float | Quantity): density (default in kg/m3)

  Returns:
      Quantity: hydraulic pressure (in bar)
  '''
  return (flsa.toUnits(H, u.m) * flsa.toUnits(rho, u.kg/u.m**3) * flsme.CTE_G).to(u.bar)

# =============================================================================
def ptoH(p: int | float | Quantity, rho: int | float | Quantity) -> Quantity:
  ''' Calculate hydraulic height from hydraulic pressure

  Args:
      p (int | float | Quantity): hydraulic pressure  (default in bar)
      rho (int | float | Quantity): density (default in kg/m3)

  Returns:
      Quantity: hydraulic height (in m)
  '''
  return (flsa.toUnits(p, u.bar) / flsa.toUnits(rho, u.kg/u.m**3) / flsme.CTE_G).to(u.m)

# =============================================================================
def Qtov(Q: int | float | Quantity, D: int | float | Quantity) -> Quantity:
  ''' Calculate velocity (in m/s) from flow rate depending on diameter.

  Args:
    Q (int | float | Quantity): Flow to convert (default in m3/h).
    D (int | float | Quantity): diameter (default in mm).

  Returns:
    Quantity: Corresponding velocity (in m/s).
  '''
  lQ = flsa.toUnits(Q, u.m**3/u.h)
  lD = flsa.toUnits(D, u.mm)
  return (lQ/ (lD**2*np.pi/4)).to(u.m/u.s)

def vtoQ(v: int | float | Quantity, D: int | float | Quantity) -> Quantity:
  ''' Calculate flow rate (in m/s) from velocity depending on diameter.

  Args:
    v (int | float | Quantity): Velocity to convert (default in m/s).
    D (int | float | Quantity): diameter (default in mm).

  Returns:
    Quantity: Corresponding flow rate (in m3/h).
  '''
  lv = flsa.toUnits(v, u.m/u.s)
  lD = flsa.toUnits(D, u.mm)
  return (lv * (lD**2*np.pi/4)).to(u.m**3/u.h)

# =============================================================================
def calcCurve(xb: Any, xe: Any, xn: Any, yfun: Any, yb: Any, ye: Any) -> Any:
  ''' Sample a function over a range and return clipped x/y arrays.

  Args:
    xb (float): Start of x range.
    xe (float): End of x range.
    xn (int): Number of sample points.
    yfun (Callable): Function mapping x values to y values.
    yb (float): Lower y clip bound.
    ye (float): Upper y clip bound.

  Returns:
    tuple[np.ndarray, np.ndarray]: Clipped x and y arrays.
  '''
  xpts = np.linspace(xb, xe, xn)
  ypts = yfun(xpts)
  if isinstance(ypts, Quantity):
    ypts = ypts.magnitude
  ypts = np.asarray(ypts)
  mask = np.logical_and(ypts >= yb, ypts <= ye)
  return xpts[mask], ypts[mask]
