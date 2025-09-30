'''
This module implements some classes that represent a hydraulic component.
The components here are passive and/or 'resistance' type ones.
Most of these classe inherit from a generic one.

'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing                 import Optional
import numpy                as np
from scipy.optimize         import fsolve
import fluids.units         as fu
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util      as flsu
import fluidsolve.medium    as flsm
import fluidsolve.comp_base as flsb
import fluidsolve.wpoint    as flswp
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity

# =============================================================================
# HYDRAULIC COMPONENT CLASSES
# =============================================================================

#******************************************************************************
# Dummy / Empty component
class Comp_Dummy(flsb.Comp_Base):
  ''' Hydraulic component representing dummy / empty / None part.

  Args:
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'group' : 'Resistance',
      'part'  : 'Dummy',
    })
    super().__init__(**args_in.restArgs())

#******************************************************************************
# Fixed static height component
class Comp_Hstatic(flsb.Comp_Base):
  ''' Hydraulic component representing a fixed static height.
      Can be a pressure (+) or a resistance (-).
      Leave the sign with the Hs to make it identical to the tube application.

  Args:
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'group' : 'Resistance',
      'part'  : 'Hstatic',
    })
    Hs_pos: str = args_in.getArg(
      'Hs_pos',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    Hs_neg: str = args_in.getArg(
      'Hs_neg',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    self._Hs: Quantity = Hs_pos - Hs_neg
    super().__init__(**args_in.restArgs())

  @property
  def Hs(self) -> Quantity:
    ''' Component static head property.

    Returns:
      Quantity: Head (in m) property.
    '''
    return self._Hs

  @Hs.setter
  def Hs(self, value: int | float | Quantity) -> None:
    ''' Set static head property.

    Args:
      value (int | float | Quantity): Static Head (default in m).
    '''
    self._Hs = flsa.toUnits(value, u.m)

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe. Here return the static height Hs.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    return -self._Hs * self._sign * self._use * use

  def calcP(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate pressure loss P in bar.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      use (int): Direction of the flow (1=as defined, -1=opposite to defined) (default to 1).
                 Keep in mind that the defined direction also can be +1 or -1.

    Returns:
      Quantity: Pressure loss P in bar.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.Htop(self.calcH(lQ, use), self._medium.rho)

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    if (self._Hs is not None):
      txt += f' Hs:{self._Hs:.2f~P} '
    return txt


#******************************************************************************
# Generic component
class Comp_Appendage (flsb.Comp_Base):
  ''' Generic resistance hydraulic component. Subclassed for specific components.

  Args:
    H (int | float | Quantity, optional): Static head (in m) when applicable.
      Defaults to None.
    L (int | float | Quantity, optional): Lenght (in m) when applicable.
      Defaults to None
    D (int | float | Quantity, optional): Diameter (in mm) when applicable.
      Defaults to None.
    e (float | Quantity, optional): epsilon - absolute wall roughness (in um) when applicable.
      Defaults to CTE_E_RVS.
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'group' : 'Resistance',
      'part'  : 'Appendage',
    })
    super().__init__(**args_in.restArgs())
    # internal variable
    self._K: float = 0.0

  @property
  def K(self) -> int | float:
    ''' Component head loss coefficient property.

    Returns:
      int | float: head loss coefficient property (-)).
    '''
    return self._K

  #@K.setter
  #def K(self, value: int | float) -> None:
  # K cannot be set

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      float: Head loss coefficient K.
    '''
    return 0.0

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.KtoH(self.calcK(lQ, use), flsu.Qtov(lQ, self._D)) * self._sign

  def calcP(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate pressure loss P in bar.

    Returns:
      Quantity: Pressure loss P in bar.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.Htop(self.calcH(lQ, use), self._medium.rho)

  def toString(self, detail=0) -> str:
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    if hasattr(self, '_L') and (self._L > 0):
      txt += f' L:{self._L:.2f~P} '
    if hasattr(self, '_D') and (self._D > 0):
      txt += f' D:{self._D:.2f~P} '
    if hasattr(self, '_Hs'):
      txt += f' Hs:{self._Hs:.2f~P} '
    if hasattr(self, '_e') and (self._e > 0):
      txt += f' e:{self._e:.2f~P} '
    return txt

#******************************************************************************
# Fixed head loss coefficient component
class Comp_Kstatic(flsb.Comp_Base):
  ''' Hydraulic component representing a fixed head loss coefficient K.

      TODO THIS IS NOT CORRECT ; also K (dimensionless) is not Kv (m3/h)
      wat is de ZIN???????????????????????????????????????????

  Args:
    K (int | float): Fixed head loss coefficient.
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'group' : 'Resistance',
      'part'  : 'Hstatic',
    })
    self._K: str = args_in.getArg(
      'K',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(int, float, need=False),
          flsa.vFun.totype(float, need=False),
      ]
    )
    super().__init__(**args_in.restArgs())

  @property
  def K(self) -> float:
    ''' Fixed head loss coefficient (K) property.

    Returns:
      float: Fixed head loss coefficient K.
    '''
    return self._K

  @K.setter
  def K(self, value: int | float) -> None:
    ''' set fixed head loss coefficient (K) property.

    Args:
      value (int | float): Fixed head loss coefficient K.
    '''
    self._K = float(value)

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K. Here just return the fixed value.

    Returns:
      float: Head loss coefficient K.
    '''
    return self._K

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return (lQ * lQ / self._K / self._K / self._medium.rho / flsm.CTE_G).to(u.m)

  def calcP(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate pressure loss P in bar.

    Returns:
      Quantity: Pressure loss P in bar.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return (lQ * lQ / self._K / self._K).to(u.bar)

#******************************************************************************
# Straight tube component
class Comp_Tube(Comp_Appendage):
  ''' Hydraulic component representing a straight tube.

  Args:
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'Tube',
    })
    self._L: str = args_in.getArg(
      'L',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    self._D: str = args_in.getArg(
      'D',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    Hs_pos: str = args_in.getArg(
      'Hs_pos',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    Hs_neg: str = args_in.getArg(
      'Hs_neg',
      [
          flsa.vFun.default(0.0 * u.m),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    self._Hs: Quantity = Hs_pos - Hs_neg
    super().__init__(**args_in.restArgs())

  @property
  def L(self) -> Quantity:
    ''' Component length property.

    Returns:
      Quantity: Length (in m) property.
    '''
    return self._L

  @L.setter
  def L(self, value: int | float | Quantity) -> None:
    ''' Set length property.

    Args:
      value (int | float | Quantity): Length (default in m).
    '''
    self._L = flsa.toUnits(value, u.m)

  @property
  def D(self) -> Quantity:
    ''' Component diameter property.

    Returns:
      Quantity: Diameter property.
    '''
    return self._D

  @D.setter
  def D(self, value: int | float | Quantity) -> None:
    ''' Set diameter property.

    Args:
      value (int | float | Quantity): Diameter (default in mm).
    '''
    self._D = flsa.toUnits(value, u.mm)

  @property
  def Hs(self) -> Quantity:
    ''' Component static head property.

    Returns:
      Quantity: Head (in m) property.
    '''
    return self._Hs

  @Hs.setter
  def Hs(self, value: int | float | Quantity) -> None:
    ''' Set static head property.

    Args:
      value (int | float | Quantity): Static Head (default in m).
    '''
    self._Hs = flsa.toUnits(value, u.m)

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Args:

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = Q.to(u.m**3/u.h) if isinstance(Q, Quantity) else Q * u.m**3/u.h
    Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D), D=self._D, rho=self._medium.rho, mu=self._medium.mu)
    Fd = fu.friction_factor(Re, eD=(self._e/self._D))
    self._K = (Fd * self._L / self._D).to_base_units()
    return self._K

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    self.calcK(lQ, 1)
    Hdyn = (8.0 * self._K * lQ * lQ / self._D / self._D / self._D / self._D / np.pi / np.pi / flsm.CTE_G).to(u.m)
    return (Hdyn - self._Hs * self._use * use) * self._sign

  def calcP(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate pressure loss P in bar.

    Returns:
      Quantity: Pressure loss P in bar.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.Htop(self.calcH(lQ, use), self._medium.rho)

#******************************************************************************
# Bend component
class Comp_Bend(Comp_Appendage):
  ''' Hydraulic component representing a pipe bend.

  Args:
    n (int, optional): Number of bends with this properties.
      Defaults to 1.
    D (int | float | Quantity, optional): Diameter (in mm).
      Defaults to 100.0*u.mm.
    A (int | float | Quantity, optional): Angle of the bend (default in degrees).
      Defaults to 90*u.degrees.
    R (int | float, optional): Bend radius (to center of pipe) in times the diameter of the pipe.
      Defaults to 1.5.
    e (float | Quantity, optional): epsilon - absolute wall roughness (in mm).
      Defaults to CTE_E_RVS.
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'Bend',
    })
    self._n: int = args_in.getArg(
      'n',
      [
          flsa.vFun.default(1),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._D: float = args_in.getArg(
      'D',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._A: Quantity = args_in.getArg(
      'A',
      [
          flsa.vFun.default(90.0 * u.degrees),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.degrees),
      ]
    )
    self._R: float = args_in.getArg(
      'R',
      [
          flsa.vFun.default(1.5),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(float),
      ]
    )
    super().__init__(**args_in.restArgs())

  @property
  def n(self) -> int:
    ''' Fixed number of bends property.

    Returns:
      int: Number of bends.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float):
    ''' set number of bends property.

    Args:
      value (int): Number of bends.
    '''
    self._n = int(value)

  @property
  def D(self) -> Quantity:
    ''' Diameter property.

    Returns:
      int: Diameter (default in mm).
    '''
    return self._D.to(u.mm)

  @D.setter
  def D(self, value: int | float | Quantity):
    ''' set diameter property.

    Args:
      value (int): Diameter.
    '''
    self._D = flsa.toUnits(value, u.mm)

  @property
  def A(self) -> Quantity:
    ''' Angle of the bend property.

    Returns:
      int: Angle of the bend (default in degrees).
    '''
    return self._A.to(u.degrees)

  @A.setter
  def A(self, value: int | float | Quantity):
    ''' set angle of the bend property.

    Args:
      value (int): Angle of the bend.
    '''
    self._A = flsa.toUnits(value, u.degrees)

  @property
  def R(self) -> int | float:
    ''' Bend radius (to center of pipe) in times the diameter of the pipe property.

    Returns:
      int: Bend radius (to center of pipe) in times the diameter of the pipe.
    '''
    return self._R

  @R.setter
  def R(self, value: int | float):
    ''' set bend radius (to center of pipe) in times the diameter of the pipe property.

    Args:
      value (int): Bend radius (to center of pipe) in times the diameter of the pipe.
    '''
    self._R = float(value)

  def calcK(self, Q: int | float | Quantity, use: int) -> int | float:
    ''' Calculate head loss coefficient K.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D), D=self._D, rho=self._medium.rho, mu=self._medium.mu)
    fd = fu.friction_factor(Re, eD=(self._e/self._D))
    return float(self._n) * fu.bend_rounded(Di=self._D, angle=self._A, fd=fd, bend_diameters=self._R)

#******************************************************************************
# Bend component
class Comp_BendLong(Comp_Appendage):
  ''' Hydraulic component representing a pipe bend.

  Args:
    D (int | float | Quantity, optional): Diameter (in mm).
      Defaults to 100.0*u.mm.
    n (int, optional): Number of bends with this properties.
      Defaults to 1.
    A (int | float | Quantity, optional): Angle of the bend (default in degrees).
      Defaults to 90*u.degrees.
    Lu (int | float, optional): Length unimpelled (in m)
      Defaults to None; then calculated with 20*D.
    e (float | Quantity, optional): epsilon - absolute wall roughness (in mm).
      Defaults to CTE_E_RVS.
  '''
  def __init__(self, **kwargs: int):
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'BendLong',
    })
    self._n: int = args_in.getArg(
      'n',
      [
          flsa.vFun.default(1),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._D: float = args_in.getArg(
      'D',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._A: Quantity = args_in.getArg(
      'A',
      [
          flsa.vFun.default(90.0 * u.degrees),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.degrees),
      ]
    )
    self._Lu: float = args_in.getArg(
      'Lu',
      [
          flsa.vFun.default(0),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m),
      ]
    )
    super().__init__(**args_in.restArgs())

  def calcK(self, Q: int | float | Quantity, use: int) -> int | float:
    ''' Calculate head loss coefficient K.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D), D=self._D, rho=self._medium.rho, mu=self._medium.mu)
    if self._Lu == 0:
      return float(self._n) * fu.bend_miter(self._A, Re=Re)
    else:
      return float(self._n) * fu.bend_miter(self._A, Re=Re, Di=self._D, L_unimpeded=self._Lu)

#******************************************************************************
# Pipe entrance component
class Comp_Entrance(Comp_Appendage):
  ''' Hydraulic component representing a pipe entrance or a pipe exit.

  Args:
    D (int | float | Quantity): Diameter (in mm).
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'Entrance',
    })
    self._D: str = args_in.getArg(
      'D',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    super().__init__(**args_in.restArgs())

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      int | float: Head loss coefficient K.
    '''
    luse = self._use * use
    if luse > 0:
      return fu.entrance_sharp()
    else:
      return fu.exit_normal()

#******************************************************************************
class Comp_SharpReduction(Comp_Appendage):
  ''' Hydraulic component representing a pipe contraction or pipe diffusor.

  Args:
    D1 (int | float | Quantity, optional): Starting diameter (in mm).
    D2 (int | float | Quantity, optional): Ending (smaller) diameter (in mm).
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'SharpReduction',
    })
    self._n: str = args_in.getArg(
      'n',
      [
          flsa.vFun.default(1),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._D1: str = args_in.getArg(
      'D1',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._D2: str = args_in.getArg(
      'D2',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    super().__init__(**args_in.restArgs())
    if self._D1 < self.D2 and self._use > 0:
      raise ValueError(f'Error: For reduction {self._name}: D1: {self._D1} must be smaller then D2:{self._D2}')
    elif self._D1 > self.D2 and self._use < 0:
      raise ValueError(f'Error: For inverse reduction {self._name}: D1: {self._D1} must be larger then D2:{self._D2}')

  @property
  def n(self) -> int:
    ''' Fixed number of bends property.

    Returns:
      int: Number of bends.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float):
    ''' set number of bends property.

    Args:
      value (int): Number of bends.
    '''
    self._n = int(value)

  @property
  def D1(self) -> int | float:
    ''' Component starting diameter property.

    Returns:
      Quantity: Starting diameter property.
    '''
    return self._D.to(u.mm)

  @D1.setter
  def D1(self, value: int | float):
    ''' Set starting diameter property.

    Args:
      value (int | float | Quantity): Starting diameter (default in mm).
    '''
    self._D1 = value
    self._D = self._D1

  @property
  def D2(self) -> int | float:
    ''' Component endingdiameter property.

    Returns:
      Quantity: Ending diameter property.
    '''
    return self._D2.to(u.mm)

  @D2.setter
  def D2(self, value: int | float):
    ''' Set diameter property.

    Args:
      value (int | float | Quantity): Diameter (default in mm).
    '''
    self._D2 = value

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      float: Head loss coefficient K.
    '''
    if self._use > 0:
      if use > 0:
        #print('c eeee1', self._D1, self._D2, fu.contraction_sharp(Di1=self._D1, Di2=self._D2))
        return fu.contraction_sharp(Di1=self._D1, Di2=self._D2)
      else:
        #print('d eeee2', self._D2, self._D1, fu.diffuser_sharp(Di1=self._D2, Di2=self._D1))
        return fu.diffuser_sharp(Di1=self._D2, Di2=self._D1)
    else:
      if use > 0:
        #print('d eeee3', self._D1, self._D2, fu.diffuser_sharp(Di1=self._D1, Di2=self._D2))
        return fu.diffuser_sharp(Di1=self._D1, Di2=self._D2)
      else:
        #print('c eeee4', self._D2, self._D1, fu.contraction_sharp(Di1=self._D2, Di2=self._D1))
        return fu.contraction_sharp(Di1=self._D2, Di2=self._D1)

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    if use == self._use:
      D = self._D1
    else:
      D = self._D2
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.KtoH(self.calcK(lQ, use), flsu.Qtov(lQ, D)) * self._sign

#******************************************************************************
class Comp_ConicalReduction(Comp_Appendage):
  ''' Hydraulic component representing a conical pipe contraction or pipe diffusor.

  Args:
    n (int | floatoptional): number of components (defaults to 1).
    D1 (int | float | Quantity, optional): Starting diameter (in mm).
    D2 (int | float | Quantity, optional): Ending (smaller) diameter (in mm).
    L (int | float | Quantity, optional): length of contraction (in mm).
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'ConicalReduction',
    })
    self._n: str = args_in.getArg(
      'n',
      [
          flsa.vFun.default(1),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._D1: str = args_in.getArg(
      'D1',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._D2: str = args_in.getArg(
      'D2',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._L: str = args_in.getArg(
      'L',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    if self._D1 < self.D2 and self._use > 0:
      raise ValueError(f'Error: For conical reduction {self._name}: D1: {self._D1} must be smaller then D2:{self._D2}')
    elif self._D1 > self.D2 and self._use < 0:
      raise ValueError(f'Error: For inverse conical reduction {self._name}: D1: {self._D1} must be larger then D2:{self._D2}')
    super().__init__(**args_in.restArgs())

  @property
  def n(self) -> int:
    ''' Fixed number of components property.

    Returns:
      int: Number of components.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float):
    ''' set number of components property.

    Args:
      value (int): Number of components.
    '''
    self._n = int(value)

  @property
  def D1(self) -> int | float:
    ''' Component starting diameter property.

    Returns:
      Quantity: Starting diameter property.
    '''
    return self._D.to(u.mm)

  @D1.setter
  def D1(self, value: int | float):
    ''' Set starting diameter property.

    Args:
      value (int | float | Quantity): Starting diameter (default in mm).
    '''
    self._D1 = value
    self._D = self._D1

  @property
  def D2(self) -> int | float:
    ''' Component endingdiameter property.

    Returns:
      Quantity: Ending diameter property.
    '''
    return self._D2.to(u.mm)

  @D2.setter
  def D2(self, value: int | float):
    ''' Set diameter property.

    Args:
      value (int | float | Quantity): Diameter (default in mm).
    '''
    self._D2 = value

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    if self._use > 0:
      if use > 0:
        Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D1), D=self._D1, rho=self._medium.rho, mu=self._medium.mu)
        fd = fu.friction_factor(Re, eD=(self._e/self._D1))
        return float(self._n) * fu.fittings.contraction_conical(Di1=self._D1, Di2=self._D2, fd=fd, l=self._L)
      else:
        Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D2), D=self._D2, rho=self._medium.rho, mu=self._medium.mu)
        fd = fu.friction_factor(Re, eD=(self._e/self._D2))
        return float(self._n) * fu.fittings.diffuser_conical(Di1=self._D2, Di2=self._D1, l=self._L, fd=fd)
    else:
      if use > 0:
        Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D1), D=self._D1, rho=self._medium.rho, mu=self._medium.mu)
        fd = fu.friction_factor(Re, eD=(self._e/self._D1))
        return float(self._n) * fu.fittings.diffuser_conical(Di1=self._D1, Di2=self._D2, l=self._L, fd=fd)
      else:
        Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D2), D=self._D2, rho=self._medium.rho, mu=self._medium.mu)
        fd = fu.friction_factor(Re, eD=(self._e/self._D2))
        return float(self._n) * fu.fittings.contraction_conical(Di1=self._D2, Di2=self._D1, fd=fd, l=self._L)

  def calcH(self, Q: int | float | Quantity, use: int) -> Quantity:
    ''' Calculate head loss H in equivalent meter pipe.

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    if use == self._use:
      D = self._D1
    else:
      D = self._D2
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.KtoH(self.calcK(lQ, use), flsu.Qtov(lQ, D)) * self._sign

#******************************************************************************
# Pipe entrance component
class C_EntranceBeveled(Comp_Appendage):
  ''' Hydraulic component representing a beveled entrance.

  Args:
    D (int | float | Quantity, optional): Diameter of pipe (in mm).
      Defaults to 100*u.mm.
    Lb (int | float | Quantity, optional): Length of bevel measured parallel to the pipe (in mm).
      Defaults to 10*u.mm.
    R (int | float | Quantity, optional): Angle of bevel with respect to the pipe length (default in degrees).
      Defaults to 45*u.degrees.

  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'EntranceBeveled',
    })
    self._D: str = args_in.getArg(
      'D',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._Lb: str = args_in.getArg(
      'Lb',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.mm),
      ]
    )
    self._R: str = args_in.getArg(
      'R',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.degrees),
      ]
    )
    super().__init__(**args_in.restArgs())

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      int | float: Head loss coefficient K.
    '''
    return fu.entrance_beveled(self._D, self._Lb, self._R, method='Rennels')

#******************************************************************************
# Plate heat exchanger component
class Comp_PHE(Comp_Appendage):
  ''' Hydraulic component representing a plate heat exchanger (PHE).

  Args:
    Nplaten (int): Number of plates.
    Npasses (int): Number of passes.
    Phi (float): Ratio of real to projected plate surface.
    Lplaat (int | float | Quantity): Plate length (default in mm).
    Bplaat (int | float | Quantity): Plate length (default in mm).
    Dkanaal (int | float | Quantity): Distance between two plates or chanel width (default in mm).
    Npoorten (int): Number of ports.
    Dpoort (int | float | Quantity): Diameter of port(default in mm).
  '''
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'PHE',
    })
    self._Nplaten: str = args_in.getArg(
      'Nplaten',
      [
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._Npasses: str = args_in.getArg(
      'Npasses',
      [
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._Phi: str = args_in.getArg(
      'Phi',
      [
          flsa.vFun.default(1.0),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(float),
      ]
    )
    self._Lplaat: str = args_in.getArg(
      'Lplaat',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tolambda(lambda x: x.to(u.mm) if isinstance(x, Quantity) else x * u.mm),
      ]
    )
    self._Bplaat: str = args_in.getArg(
      'Bplaat',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tolambda(lambda x: x.to(u.mm) if isinstance(x, Quantity) else x * u.mm),
      ]
    )
    self._Dkanaal: str = args_in.getArg(
      'Dkanaal',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tolambda(lambda x: x.to(u.mm) if isinstance(x, Quantity) else x * u.mm),
      ]
    )
    self._Npoorten: str = args_in.getArg(
      'Npoorten',
      [
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._Dpoort: str = args_in.getArg(
      'Dpoort',
      [
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tolambda(lambda x: x.to(u.mm) if isinstance(x, Quantity) else x * u.mm),
      ]
    )
    super().__init__(**args_in.restArgs())

  def calcK(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss coefficient K.
        Speed is fictional, calculated with met Dpoort.

    Args:
      Q (int | float | Quantity, optional): Flow rate (default in m3/h).
        Defaults to 0.0*u.m**3/u.h.

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = Q.to(u.m**3/u.h) if isinstance(Q, Quantity) else Q * u.m**3/u.h
    v = lQ / (self._Dpoort**2*np.pi/4)
    return (self.calcH(lQ) * 2 * flsm.CTE_G / v)

  def calcH(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss H in equivalent meter pipe.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = Q.to(u.m**3/u.h) if isinstance(Q, Quantity) else Q * u.m**3/u.h
    # drukval in de kanalen
    Dh = 2*self._Dkanaal/self._Phi
    #print(f'Dh= {Dh:.2f~P}')
    Ncp = (self._Nplaten-1)/(2*self._Npasses)
    #print(f'Ncp= {Ncp:.1f}')
    Gc = (lQ*self._medium.rho / (Ncp*self._Dkanaal*self._Bplaat)).to_base_units()
    #print(f'Gc= {Gc:.3f~P}')
    Re = (Gc*Dh/self._medium.mu).to_base_units()
    Re_m = Re.magnitude
    #print(f'Re= {Re:.0f~P}')
    f = np.where(Re_m < 200, 19.4*Re_m**(-0.589), 2.99*Re_m**(-0.183))
    #print(f'f= {f:.4f}')
    P_kanalen = (4*f*self._Lplaat*self._Npasses/Dh*Gc**2/2/self._medium.rho*(1)**(-0.17)).to('Pa')
    #print(f'kanalen= {P_kanalen}')
    # drukval in de poorten
    P_poorten = (11.2 * 2 * self._medium.rho * lQ**2 / np.pi**2 / self._Dpoort**4).to('Pa')
    #print(f'P poorten= {P_poorten}')
    return fu.head_from_P(P=P_kanalen + P_poorten, rho=self._medium.rho).to(u.m)

  def calcH(self, Q: int | float | Quantity, use: int) -> float:
    ''' Calculate head loss H in equivalent meter pipe.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      Quantity: Head loss H (in equivalent meter pipe).
    '''
    lQ = Q.to(u.m**3/u.h) if isinstance(Q, Quantity) else Q * u.m**3/u.h
    # drukval in de kanalen
    Dh = 2*self._Dkanaal/self._Phi
    #print(f'Dh= {Dh:.2f~P}')
    Ncp = (self._Nplaten-1)/(2*self._Npasses)
    #print(f'Ncp= {Ncp:.1f}')
    Gc = (lQ*self._medium.rho / (Ncp*self._Dkanaal*self._Bplaat)).to_base_units()
    #print(f'Gc= {Gc:.3f~P}')
    Re = (Gc*Dh/self._medium.mu).to_base_units()
    Re_m = Re.magnitude
    #print(f'Re= {Re:.0f~P}')
    f = np.where(Re_m < 200, 19.4*Re_m**(-0.589), 2.99*Re_m**(-0.183))
    #print(f'f= {f:.4f}')
    P_kanalen = (4*f*self._Lplaat*self._Npasses/Dh*Gc**2/2/self._medium.rho*(1)**(-0.17)).to('Pa')
    #print(f'kanalen= {P_kanalen}')
    # drukval in de poorten
    P_poorten = (11.2 * 2 * self._medium.rho * lQ**2 / np.pi**2 / self._Dpoort**4).to('Pa')
    #print(f'P poorten= {P_poorten}')
    return fu.head_from_P(P=P_kanalen + P_poorten, rho=self._medium.rho).to(u.m) * self._sign

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    txt += f' Nplaten: {self._Nplaten}, Npasses: {self._Npasses}, Phi: {self._Phi}'
    txt += f' Lplaat: {self._Lplaat:.1f~P}, Bplaat: {self._Bplaat:.1f~P}, Dkanaal: {self._Dkanaal:.1f~P}'
    txt += f' Npoorten: {self._Npoorten}, Dpoort: {self._Dpoort:.1f~P}\n'
    return txt
#******************************************************************************
# Serial combination component
class Comp_Serial (Comp_Appendage):
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'SERIAL',
    })
    self._items : list =args_in.getArg(
      'item',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    super().__init__(**args_in.restArgs())
    for c in self._items:
      c.medium = self._medium

  def addItem(self, item: flsb.Comp_Base):
    self._items.append(item)
    item.medium = self._medium
    return item

  def setItem(self, idx: int, item: flsb.Comp_Base):
    self._items[idx] = item
    item.medium = self._medium
    return item

  def getItem(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def getItems(self) -> list:
    return self._items

  def calcH(self, Q: int | float | Quantity, use: int):
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return sum([item.calcH(lQ, use) for item in self._items])

  def calcHprofile(self, Q, use: int, incr: bool=False):
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    pts = []
    H = 0 *u.m
    for i in range(len(self._items)):
      item = self._items[i]
      if incr:
        H = H + item.calcH(lQ, use)
      else:
        H = item.calcH(lQ, use)
      pts.append(flswp.Wpoint(name=f'{i}:{item.name}', Q=lQ, H=H))
    H = self.calcH(lQ, use)
    pts.append(flswp.Wpoint(name='Tot', Q=lQ, H=H))
    return pts

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    for i in range(len(self._items)):
      txt += f' {i}: {self._items[i]}\n'
    return txt


#******************************************************************************
# Parallel combination component
class Comp_Parallel (Comp_Appendage):
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'PARALLEL',
    })
    self._guess : int | float | list =args_in.getArg(
      'guess',
      [
          flsa.vFun.default(1.0),
          flsa.vFun.istype(int, float, list),
      ]
    )
    self._items : list =args_in.getArg(
      'item',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    super().__init__(**args_in.restArgs())
    for c in self._items:
      c.medium = self._medium
    self._H = None
    self._Q = None
    self._infodict = {}

  @property
  def guess(self) -> int:
    ''' Guess for fsolve.

    Returns:
      int | float | list: Guess.
    '''
    return self._guess

  @guess.setter
  def guess(self, value: int | float | list):
    ''' set guess for fsolve.

    Args:
      value (int | float | list): Guess.
    '''
    self._guess = value

  def addItem(self, item: flsb.Comp_Base):
    self._items.append(item)
    item.medium = self._medium
    return item

  def setItem(self, idx: int, item: flsb.Comp_Base):
    self._items[idx] = item
    item.medium = self._medium
    return item

  def getItem(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def getItems(self) -> list:
    return self._items

  def getH(self):
    return self._H

  def getQ(self):
    return self._Q

  def calcH(self, Q: int | float | Quantity, use: int):

    def F(Q: list[float], Qtot: int | float) -> list[float]:
      ''' fsolve system of equations. The result of the equations needs te evolve to zeros.

      Args:
          Q (list[float]): guess for flow in each branch (in m3/h)
          Qtot (int | float): total flow (in m3/h)

      Returns:
          list[float]: list with:
                        differences in head loss between branch n and branch n+1 and total flow
                        difference between sum of branch flows and total flow
      '''
      res = []
      for n in range(top):
        res.append(self._items[n].calcH(Q[n], use).magnitude - self._items[n+1].calcH(Q[n+1], use).magnitude)
      res.append(sum(Q) - Qtot)
      return res

    lQ = flsa.toUnits(Q, u.m**3/u.h, magnitude=True)
    # number of equations
    n_items = len(self._items)
    top = n_items - 1
    # Initial guess
    initial_guess = None
    if isinstance(self._guess, (int, float)):
      initial_guess = [self._guess] * (n_items)
    elif isinstance(self._guess, list):
      if len(self._guess) != n_items:
        raise ValueError(f'Initial guess length {len(self._guess)} does not match number of equations: {n_items}')
      initial_guess = self._guess
    # Solve the system of equations
    result, self._infodict, ier, msg = fsolve(func=F, x0=initial_guess, args=lQ, full_output=1)
    if ier != 1:
      raise ValueError(f'Error in Parallel Component "{self._name}".calcH: {msg}')
    # process result
    self._Q = result *u.m**3/u.h
    self._H = [0.0] * n_items
    for i in range(len(self._items)):
      self._H[i] = self._items[i].calcH(result[i], use)
    return self._H[0]

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    for i in range(len(self._items)):
      txt += f' {i}: {self._items[i]}\n'
    return txt

#******************************************************************************
# Parallel combination component
class Comp_Parallel2 (Comp_Appendage):
  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    args_in.addArgs({
      'part'  : 'PARALLEL2',
    })
    self._initguess : float =args_in.getArg(
      'guess',
      [
          flsa.vFun.default(1.0),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(float),
      ]
    )
    self._items : list =args_in.getArg(
      'item',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    super().__init__(**args_in.restArgs())
    for c in self._items:
      c.medium = self._medium
    #
    self._H = [0.0, 0.0] *u.m
    self._Q = [0.0, 0.0] *u.m**3/u.h
    self._infodict = {}

  @property
  def guess(self) -> float:
    ''' Guess for fsolve.

    Returns:
      float : Guess.
    '''
    return self._initguess

  @guess.setter
  def guess(self, value: int | float | list):
    ''' set guess for fsolve.

    Args:
      value (int | float | list): Guess.
    '''
    self._initguess = float(value)

  def addItem(self, item: flsb.Comp_Base):
    self._items.append(item)
    item.medium = self._medium
    return item

  def setItem(self, idx: int, item: flsb.Comp_Base):
    self._items[idx] = item
    item.medium = self._medium
    return item

  def getItem(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def getItems(self) -> list:
    return self._items

  def getH(self):
    return self._H

  def getQ(self):
    return self._Q

  def calcH(self, Q: int | float | Quantity, use: int):

    def F(Q1: float, Qtot: int | float):
      ''' fsolve system of equations. The result of the equations needs te evolve to zeros.

      Args:
          Q1 (float): guess for flow in branch 1 (in m3/h)
          Qtot (int | float): total flow (in m3/h)

      Returns:
          float: differences in head loss between the two branches.
      '''
      H0 = self._items[0].calcH(Q1, use)
      H1 = self._items[1].calcH(Qtot-Q1, use)
      return (H0-H1).magnitude

    lQ = flsa.toUnits(Q, u.m**3/u.h, magnitude=True)
    # Solve the system of equations
    result, self._infodict, ier, msg = fsolve(func=F, x0=self._initguess, args=lQ, full_output=1)
    if ier != 1:
      raise ValueError(f'Error in Parallel Component "{self._name}".calcH: {msg}')
    # process result
    self._Q = [result[0] *u.m**3/u.h, (lQ - result[0]) *u.m**3/u.h]
    self._H = [self._items[0].calcH(self._Q[0], use), self._items[1].calcH(self._Q[1], use)]
    return self._H[0]

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    for i in range(len(self._items)):
      txt += f' {i}: {self._items[i]}\n'
    return txt