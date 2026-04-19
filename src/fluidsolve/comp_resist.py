'''
Passive hydraulic resistance components.
Most classes in this module inherit from generic base component types.

This module groups components that consume energy in a hydraulic network,
such as static head terms, generic appendages, pipes, bends, reducers,
orifices, and other flow resistances.

Main component families in this module include:

* fixed static head elements,
* generic appendage-based loss models,
* tube and fitting components parameterized by geometry,
* loss elements that can be derived from working-point or coefficient data.

Design rules:

* Mounting direction is port 1 -> port 2.
* Flow direction is given by ``sense``.
* ``sense = +1`` means flow follows mounting direction.
* ``sense = -1`` means flow is opposite to mounting direction.

In practice, most classes in this module implement one of these patterns:

* a fixed head contribution,
* a resistance coefficient or loss relation,
* a geometry-dependent pressure drop derived from diameter, length,
  roughness, and medium properties.

Modeling intent:

* Use these classes to represent passive losses in branches and loops.
* Combine with pump/source components from other modules for full systems.
* Keep ``sense`` explicit when assembling networks so directional loss signs
  stay consistent in both continuity and loop-energy equations.

These classes are intended to be combined inside a network where topology is
handled by the network model and the local hydraulic behavior is handled by
the component itself.

Typical usage:

1. Create a resistance component with its geometric or catalogue data.
2. Set the medium if different from the default.
3. Use ``calcH`` or ``calcP`` to evaluate the hydraulic loss for a flow rate.
4. Insert the component into a network segment.

Example::

  comp = Comp_Hstatic(Hs_pos=3 * u.m)
  head = comp.calcH(1.2 * u.m**3 / u.h, sense=1)

The sign conventions in this module are chosen to stay consistent with the
rest of fluidsolve, especially when the same component is traversed in either
direction during network solving.

For advanced usage, several classes expose helper methods for coefficient
evaluation, making it easier to calibrate components from measured data or
catalogue values before running a network solve.
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
import numpy as np
from scipy.optimize import fsolve
import fluids.units as fu
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.util      as flsu
import fluidsolve.medium    as flsme
import fluidsolve.comp_base as flsb
import fluidsolve.wpoint    as flswp
# units
u        = flsme.unitRegistry
Quantity = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# STATIC HEIGHT
# =============================================================================
class Comp_Hstatic(flsb.Comp_Base):  # pylint: disable=invalid-name
  ''' Hydraulic component representing fixed static head.
  Can be a pressure source (+) or a resistance term (-).

  Args:
    Hs_pos (int | float | Quantity, optional): Positive (source) static head (default in m).
    Hs_neg (int | float | Quantity, optional): Negative (resistance) static head (default in m).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Resistance'
  _part   : str = 'Hstatic'
  _prefix : str = 'Hs'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # reservation for child classes
    self.L = None
    self.D = None
    # arguments
    args_in = flsa.GetArgs(kwargs)
    Hs_pos = args_in.getArg(
      'Hs_pos',
      [flsa.vFun.default(0.0*u.m),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.m)]
    )
    Hs_neg = args_in.getArg(
      'Hs_neg',
      [flsa.vFun.default(0.0*u.m),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.m)]
    )
    self._Hs = Hs_pos - Hs_neg
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
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

  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    '''
    Static head contribution.
    '''
    psense = 1 if pin < pout else -1
    return -self._Hs * self._sign * sense * psense

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
    txt = super().toString(sdetail) + '\n'
    if self._Hs is not None:
      txt += f' Hs:{self._Hs:.2f~P} '
    return txt

# =============================================================================
# GENERIC APPENDAGE
# =============================================================================
class Comp_Appendage(flsb.Comp_Base):  # pylint: disable=invalid-name
  ''' Generic resistance component class.

  Args:
    H (int | float | Quantity, optional): Static head when applicable.
    L (int | float | Quantity, optional): Length when applicable.
    D (int | float | Quantity, optional): Diameter when applicable.
    e (float | Quantity, optional): Absolute wall roughness when applicable.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _group  : str = 'Resistance'
  _part   : str = 'Appendage'
  _prefix : str = 'R'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # base class init
    super().__init__(**kwargs)
    # Preserve child-provided geometry when set before super().__init__.
    if not hasattr(self, '_L'):
      self._L = None
    if not hasattr(self, '_D'):
      self._D = None
    # internal variable
    self._K = 0.0

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def K(self) -> int | float:
    ''' Component head loss coefficient property.

    Returns:
      int | float: Head loss coefficient.
    '''
    return self._K

  #@K.setter
  #def K(self, value: int | float) -> None:
  # K cannot be set

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout:int=2) -> float:  # pylint: disable=unused-argument
    '''
    Head loss coefficient.
    Override in subclasses.
    '''
    return 0.0

  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    '''Calculate head loss from loss coefficient and flow velocity.

    Args:
      Q (Quantity): Flow rate.
      sense (int, optional): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      Quantity: Head loss in equivalent meters of fluid.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return flsu.KtoH(self.calcK(lQ, sense, pin, pout), flsu.Qtov(lQ, self._D)) * self._sign

  def toString(self, detail: int=0) -> str:
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    if (self._L is not None) and (self._L > 0):
      txt += f' L:{self._L:.2f~P} '
    if (self._D is not None) and (self._D > 0):
      txt += f' D:{self._D:.2f~P} '
    if hasattr(self, '_Hs'):
      txt += f' Hs:{self._Hs:.2f~P} '
    if hasattr(self, '_e') and (self._e > 0):
      txt += f' e:{self._e:.2f~P} '
    return txt

# =============================================================================
# STRAIGHT TUBE
# =============================================================================
class Comp_Tube(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Straight pipe component with friction and static head.

  Args:
    L (int | float | Quantity): Pipe length (default in m).
    D (int | float | Quantity): Inner diameter (default in mm).
    Hs_pos (int | float | Quantity, optional): Positive static head (default in m).
    Hs_neg (int | float | Quantity, optional): Negative static head (default in m).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Tube'
  _prefix : str = 'Tu'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._L = args_in.getArg(
      'L',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.m)]
    )
    self._D = args_in.getArg(
      'D',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    Hs_pos = args_in.getArg(
      'Hs_pos',
      [flsa.vFun.default(0.0*u.m),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.m)]
    )
    Hs_neg = args_in.getArg(
      'Hs_neg',
      [flsa.vFun.default(0.0*u.m),
       flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.m)]
    )
    self._Hs = Hs_pos - Hs_neg
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
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

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D), D=self._D, rho=self._medium.rho, mu=self._medium.mu)
    fd = fu.friction_factor(Re, eD=self._e/self._D)
    self._K = (fd * self._L / self._D).to_base_units()
    return self._K

  def calcH(self, Q: Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate head loss in equivalent meters of fluid.

    Returns:
      Quantity: Head loss in equivalent meters of fluid.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    self.calcK(lQ, 1)
    Hdyn = (8.0 * self._K * lQ*lQ / (self._D**4 * np.pi**2 * flsme.CTE_G)).to(u.m)
    psense = 1 if pin < pout else -1
    return (Hdyn - self._Hs * sense * psense) * self._sign

# =============================================================================
# BEND
# =============================================================================
class Comp_Bend(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Hydraulic component representing a pipe bend.

  Args:
    n (int, optional): Number of bends with these properties.
    D (int | float | Quantity, optional): Diameter (mm).
    A (int | float | Quantity, optional): Bend angle (degrees).
    R (int | float, optional): Bend radius (to center of pipe) in times the diameter of the pipe.
    e (float | Quantity, optional): Absolute wall roughness.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'Bend'
  _prefix : str = 'B'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def n(self) -> int:
    ''' Fixed number of bends property.

    Returns:
      int: Number of bends.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float) -> Any:
    ''' Set number of bends property.

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
  def D(self, value: int | float | Quantity) -> Any:
    ''' Set diameter property.

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
  def A(self, value: int | float | Quantity) -> Any:
    ''' Set bend angle property.

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
  def R(self, value: int | float) -> Any:
    ''' Set bend radius property.

    Args:
      value (int): Bend radius (to center of pipe) in times the diameter of the pipe.
    '''
    self._R = float(value)

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2) -> int | float:
    ''' Calculate head loss coefficient K.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D), D=self._D, rho=self._medium.rho, mu=self._medium.mu)
    fd = fu.friction_factor(Re, eD=self._e/self._D)
    return float(self._n) * fu.bend_rounded(Di=self._D, angle=self._A, fd=fd, bend_diameters=self._R)

# =============================================================================
# LONG BEND
# =============================================================================
class Comp_BendLong(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Hydraulic component representing a pipe bend.

  Args:
    D (int | float | Quantity, optional): Diameter (in mm).
      Defaults to 100.0*u.mm.
    n (int, optional): Number of bends with these properties.
    A (int | float | Quantity, optional): Bend angle (degrees).
    Lu (int | float, optional): Unimpeded length (m).
    e (float | Quantity, optional): Absolute wall roughness.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'BendLong'
  _prefix : str = 'B'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2) -> int | float:
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

# =============================================================================
# PIPE ENTRANCE - EXIT
# =============================================================================
class Comp_Entrance(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Pipe entrance (or exit under reversed flow) component.

  Args:
    D (int | float | Quantity): Diameter (in mm).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'Entrance'
  _prefix : str = 'E'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)

    self._D = args_in.getArg(
      'D',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    '''Calculate entrance or exit loss coefficient.

    Args:
      Q (Quantity): Flow rate.
      sense (int): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      float: Loss coefficient for the active flow direction.
    '''
    if (sense > 0 and pin < pout) or (sense < 0 and pin > pout):
      return fu.entrance_sharp()
    else:
      return fu.exit_normal()

# =============================================================================
# PIPE SHARP REDUCTION - DIFFUSOR
# =============================================================================
class Comp_SharpReduction(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Pipe contraction (or diffuser under reversed flow) component.

  Args:
    D1 (int | float | Quantity): Starting (larger) diameter (in mm).
    D2 (int | float | Quantity): Ending (smaller) diameter (in mm).
    n (int, optional): Number of instances in series.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part   : str = 'SharpReduction'
  _prefix : str = 'Re'

  def __init__(self, **kwargs: Any) -> Any:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._n: str = args_in.getArg(
      'n',
      [
          flsa.vFun.default(1),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._D1 = args_in.getArg(
      'D1',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    self._D2 = args_in.getArg(
      'D2',
      [flsa.vFun.istype(int, float, Quantity),
       flsa.vFun.tounits(u.mm)]
    )
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    if self._D1 < self.D2:
      raise ValueError(f'Error: For sharp reduction {self._name}: D1: {self._D1} must be larger than D2:{self._D2}')

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def n(self) -> int:
    ''' Fixed number of components property.

    Returns:
      int: Number of components.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float) -> Any:
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
    return self._D1.to(u.mm)

  @D1.setter
  def D1(self, value: int | float) -> Any:
    ''' Set starting diameter property.

    Args:
      value (int | float | Quantity): Starting diameter (default in mm).
    '''
    self._D1 = flsa.toUnits(value, u.mm)

  @property
  def D2(self) -> int | float:
    ''' Component ending diameter property.

    Returns:
      Quantity: Ending diameter property.
    '''
    return self._D2.to(u.mm)

  @D2.setter
  def D2(self, value: int | float) -> Any:
    ''' Set diameter property.

    Args:
      value (int | float | Quantity): Diameter (default in mm).
    '''
    self._D2 = value

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    '''Calculate contraction or diffuser loss coefficient.

    Args:
      Q (Quantity): Flow rate.
      sense (int): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      float: Loss coefficient for the active flow direction.
    '''
    if (sense > 0 and pin < pout) or (sense < 0 and pin > pout):
      return float(self._n) * fu.contraction_sharp(Di1=self._D1, Di2=self._D2)
    else:
      return float(self._n) * fu.diffuser_sharp(Di1=self._D2, Di2=self._D1)

  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Quantity:
    ''' Calculate head loss in equivalent meters of fluid.

    Returns:
      Quantity: Head loss in equivalent meters of fluid.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    #if sense > 0:
    #  D = self._D1
    #else:
    #  D = self._D2
    return flsu.KtoH(self.calcK(lQ, sense, pin, pout), flsu.Qtov(lQ, self._D1)) * self._sign

# =============================================================================
# PIPE CONICAL REDUCTION - DIFFUSOR
# =============================================================================
class Comp_ConicalReduction(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Conical contraction (or diffuser under reversed flow) component.

  Args:
    n (int | float, optional): Number of components.
    D1 (int | float | Quantity, optional): Starting diameter (mm).
    D2 (int | float | Quantity, optional): Ending diameter (mm).
    L (int | float | Quantity, optional): Contraction length (mm).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'ConicalReduction'
  _prefix : str = 'Re'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
          flsa.vFun.tounits(u.m),
      ]
    )
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    if self._D1 < self.D2:
      raise ValueError(f'Error: For conical reduction {self._name}: D1: {self._D1} must be larger than D2:{self._D2}')

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def n(self) -> int:
    ''' Fixed number of components property.

    Returns:
      int: Number of components.
    '''
    return self._n

  @n.setter
  def n(self, value: int | float) -> Any:
    ''' Set number of components property.

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
    return self._D1.to(u.mm)

  @D1.setter
  def D1(self, value: int | float) -> Any:
    ''' Set starting diameter property.

    Args:
      value (int | float | Quantity): Starting diameter (default in mm).
    '''
    self._D1 = flsa.toUnits(value, u.mm)

  @property
  def D2(self) -> int | float:
    ''' Component ending diameter property.

    Returns:
      Quantity: Ending diameter property.
    '''
    return self._D2.to(u.mm)

  @D2.setter
  def D2(self, value: int | float) -> Any:
    ''' Set diameter property.

    Args:
      value (int | float | Quantity): Diameter (default in mm).
    '''
    self._D2 = value

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      float: Head loss coefficient K.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    if (sense > 0 and pin < pout) or (sense < 0 and pin > pout):
      Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D1), D=self._D1, rho=self._medium.rho, mu=self._medium.mu)
      fd = fu.friction_factor(Re, eD=self._e/self._D1)
      return float(self._n) * fu.fittings.contraction_conical(Di1=self._D1, Di2=self._D2, fd=fd, l=self._L)
    else:
      Re = fu.Reynolds(V=flsu.Qtov(lQ, self._D2), D=self._D2, rho=self._medium.rho, mu=self._medium.mu)
      fd = fu.friction_factor(Re, eD=self._e/self._D2)
      return float(self._n) * fu.fittings.diffuser_conical(Di1=self._D2, Di2=self._D1, l=self._L, fd=fd)

# =============================================================================
# PIPE BEVELED ENTRANCE - EXIT
# =============================================================================
class C_EntranceBeveled(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Hydraulic component representing a beveled entrance.
  Reverse-flow behavior is not implemented.

  Args:
    D (int | float | Quantity, optional): Pipe diameter (mm).
    Lb (int | float | Quantity, optional): Bevel length measured parallel to the pipe (mm).
    R (int | float | Quantity, optional): Bevel angle with respect to pipe axis (degrees).

  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'EntranceBeveled'
  _prefix : str = 'E'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
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
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    ''' Calculate head loss coefficient K.

    Returns:
      int | float: Head loss coefficient K.
    '''
    if (sense > 0 and pin < pout) or (sense < 0 and pin > pout):
      return fu.entrance_beveled(self._D, self._Lb, self._R, method='Rennels')
    else:
      raise ValueError(f'Reverse flow not implemented in Component "{self._name}"')

# =============================================================================
# PLATE HEAT EXCHANGER (PHE)
# =============================================================================
class Comp_PHE(Comp_Appendage):  # pylint: disable=invalid-name
  ''' Hydraulic component representing a plate heat exchanger (PHE).

  Args:
    Nplaten (int): Number of plates.
    Npasses (int): Number of passes.
    Phi (float): Ratio of real to projected plate surface.
    Lplaat (int | float | Quantity): Plate length (default in mm).
    Bplaat (int | float | Quantity): Plate length (default in mm).
    Dkanaal (int | float | Quantity): Distance between two plates or channel width (mm).
    Npoorten (int): Number of ports.
    Dpoort (int | float | Quantity): Port diameter (mm).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'PHE'
  _prefix : str = 'PHE'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
    # base class init
    super().__init__(**args_in.restArgs())

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcK(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2) -> float:
    ''' Calculate head loss coefficient K.
        Speed is a derived value calculated using Dpoort.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      int | float: Head loss coefficient K.
    '''
    lQ = Q.to(u.m**3/u.h) if isinstance(Q, Quantity) else Q * u.m**3/u.h
    v = lQ / (self._Dpoort**2*np.pi/4)
    return (self.calcH(lQ, sense, pin, pout) * 2 * flsme.CTE_G / (v**2)).to_base_units().magnitude

  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> float:
    ''' Calculate head loss in equivalent meters of fluid.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).

    Returns:
      Quantity: Head loss in equivalent meters of fluid.
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
    txt = super().toString(sdetail) + '\n'
    txt += f' Nplaten: {self._Nplaten}, Npasses: {self._Npasses}, Phi: {self._Phi}'
    txt += f' Lplaat: {self._Lplaat:.1f~P}, Bplaat: {self._Bplaat:.1f~P}, Dkanaal: {self._Dkanaal:.1f~P}'
    txt += f' Npoorten: {self._Npoorten}, Dpoort: {self._Dpoort:.1f~P}\n'
    return txt

# =============================================================================
# SERIAL COMBINATION OF COMPONENTS
# =============================================================================
class Comp_Serial (Comp_Appendage):  # pylint: disable=invalid-name
  ''' Serial combination of components.

  Args:
    item (list, optional): List of Comp_Base components to connect in series.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'SERIAL'
  _prefix : str = 'ser'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._items : list =args_in.getArg(
      'item',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    for c in self._items:
      c.medium = self._medium

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def Components(self) -> list:
    return self._items

  def getComp(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def setComp(self, idx: int, item: flsb.Comp_Base) -> Any:
    self._items[idx] = item
    # item.medium = self._medium So item.medium = ... is illegal by design.
    return item

  def addComp(self, item: flsb.Comp_Base) -> Any:
    self._items.append(item)
    # item.medium = self._medium So item.medium = ... is illegal by design.
    return item

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Any:
    '''Calculate total head change across all series components.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      sense (int, optional): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      Any: Summed head change across all components.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    return sum([item.calcH(lQ, sense, pin, pout) for item in self._items])

  def calcHprofile(self, Q: int | float | Quantity, sense: int, pin: int=1, pout:int=2, incr: bool=False) -> Any:
    '''Calculate per-component head profile for a given flow.

    Args:
      Q (int | float | Quantity): Flow rate (default in m3/h).
      sense (int): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.
      incr (bool, optional): If True, accumulate head over the series.

    Returns:
      Any: List of working-point entries for each component and total.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    pts = []
    H = 0 *u.m
    for i, item in enumerate(self._items):
      if incr:
        H = H + item.calcH(lQ, sense, pin, pout)
      else:
        H = item.calcH(lQ, sense, pin, pout)
      pts.append(flswp.Wpoint(name=f'{i}:{item.name}', Q=lQ, H=H))
    H = self.calcH(lQ, sense, pin, pout)
    pts.append(flswp.Wpoint(name='Tot', Q=lQ, H=H))
    return pts

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
    txt = super().toString(sdetail) + '\n'
    for i, item in enumerate(self._items):
      txt += f' {i}: {item}\n'
    return txt

# =============================================================================
# PARALLEL COMBINATION OF COMPONENTS
# =============================================================================
class Comp_Parallel (Comp_Appendage):  # pylint: disable=invalid-name
  ''' Parallel combination of components.

  Args:
    item (list, optional): List of Comp_Base components to connect in parallel.
    guess (int | float | list, optional): Initial flow guess for the solver (in m3/h).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'PARALLEL'
  _prefix : str = 'par'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    for c in self._items:
      c.medium = self._medium
    self._H = None
    self._Q = None
    self._infodict = {}

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def guess(self) -> int:
    ''' Guess for fsolve.

    Returns:
      int | float | list: Guess.
    '''
    return self._guess

  @guess.setter
  def guess(self, value: int | float | list) -> Any:
    ''' Set initial guess for fsolve.

    Args:
      value (int | float | list): Guess.
    '''
    self._guess = value

  @property
  def Components(self) -> list:
    return self._items

  def getComp(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def setComp(self, idx: int, item: flsb.Comp_Base) -> Any:
    self._items[idx] = item
    item.medium = self._medium
    return item

  def addComp(self, item: flsb.Comp_Base) -> Any:
    self._items.append(item)
    #item.medium = self._medium
    return item

  def getH(self) -> Any:
    return self._H

  def getQ(self) -> Any:
    return self._Q

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Any:
    '''Solve branch flows and return common head loss for parallel components.

    Args:
      Q (int | float | Quantity): Total flow rate (default in m3/h).
      sense (int, optional): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      Any: Common head value for the parallel block.
    '''

    def F(Q: list[float], Qtot: int | float) -> list[float]:
      ''' fsolve system of equations.
      Residuals should converge to zero.

      Args:
          Q (list[float]): guess for flow in each branch (in m3/h)
          Qtot (int | float): total flow (in m3/h)

      Returns:
          list[float]: Residual list with:
            differences in head loss between adjacent branches,
            and the flow balance residual.
      '''
      res = []
      for n in range(top):
        res.append(self._items[n].calcH(Q[n], sense, pin, pout).magnitude - self._items[n+1].calcH(Q[n+1], sense, pin, pout).magnitude)
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
    for i, item in enumerate(self._items):
      self._H[i] = item.calcH(result[i], sense, pin, pout)
    return self._H[0]

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
    txt = super().toString(sdetail) + '\n'
    for i, item in enumerate(self._items):
      txt += f' {i}: {item}\n'
    return txt

# =============================================================================
# PARALLEL COMBINATION OF EXACT 2 COMPONENTS
# =============================================================================
class Comp_Parallel2 (Comp_Appendage):  # pylint: disable=invalid-name
  ''' Parallel combination of exactly two components.

  Args:
    item (list, optional): List of exactly two Comp_Base components to connect in parallel.
    guess (int | float, optional): Initial flow guess for the solver (in m3/h).
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES
  _part : str = 'PARALLEL2'
  _prefix : str = 'par2'

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: int) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
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
          #flsa.vFun.haslen(2), # can also be defined later on
      ]
    )
    # base class init
    super().__init__(**args_in.restArgs())
    # some calculations
    for c in self._items:
      c.medium = self._medium
    #
    self._H = [0.0, 0.0] *u.m
    self._Q = [0.0, 0.0] *u.m**3/u.h
    self._infodict = {}

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def guess(self) -> float:
    ''' Guess for fsolve.

    Returns:
      float : Guess.
    '''
    return self._initguess

  @guess.setter
  def guess(self, value: int | float | list) -> Any:
    ''' Set initial guess for fsolve.

    Args:
      value (int | float | list): Guess.
    '''
    self._initguess = float(value)

  @property
  def Components(self) -> list:
    return self._items

  def getComp(self, idx: int) -> flsb.Comp_Base:
    return self._items[idx]

  def setComp(self, idx: int, item: flsb.Comp_Base) -> Any:
    self._items[idx] = item
    item.medium = self._medium
    return item

  def addComp(self, item: flsb.Comp_Base) -> Any:
    self._items.append(item)
    item.medium = self._medium
    return item

  def getH(self) -> Any:
    return self._H

  def getQ(self) -> Any:
    return self._Q

  # --------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2) -> Any:
    '''Solve flow split for two parallel branches and return common head.

    Args:
      Q (int | float | Quantity): Total flow rate (default in m3/h).
      sense (int, optional): Flow direction indicator.
      pin (int, optional): Inlet port index.
      pout (int, optional): Outlet port index.

    Returns:
      Any: Common head value for the two-branch parallel block.
    '''

    def F(Q1: float, Qtot: int | float) -> Any:
      ''' fsolve equation for two parallel branches.

      Args:
          Q1 (float): guess for flow in branch 1 (in m3/h)
          Qtot (int | float): total flow (in m3/h)

      Returns:
            float: Head-loss difference between the two branches.
      '''
      H0 = self._items[0].calcH(Q1, sense, pin, pout)
      H1 = self._items[1].calcH(Qtot-Q1, sense, pin, pout)
      return (H0-H1).magnitude

    lQ = flsa.toUnits(Q, u.m**3/u.h, magnitude=True)
    # Solve the system of equations
    result, self._infodict, ier, msg = fsolve(func=F, x0=self._initguess, args=lQ, full_output=1)
    if ier != 1:
      raise ValueError(f'Error in Parallel Component "{self._name}".calcH: {msg}')
    # process result
    self._Q = [result[0] *u.m**3/u.h, (lQ - result[0]) *u.m**3/u.h]
    self._H = [self._items[0].calcH(self._Q[0], sense, pin, pout), self._items[1].calcH(self._Q[1], sense, pin, pout)]
    return self._H[0]

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
    txt = super().toString(sdetail) + '\n'
    for i, item in enumerate(self._items):
      txt += f' {i}: {item}\n'
    return txt
