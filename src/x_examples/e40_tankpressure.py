'''
  e40_tankpressure.py

  Local tank component example.
  Demonstrates dynamic registration of a custom Comp_Base-derived component.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
from typing import Any
import math
import fluids.units as fu
import fluidsolve   as fls
import fluidsolve.comp_base as flsb
import fluidsolve.medium as flsm
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]


# =============================================================================
# LOCAL COMPONENT: TANK
# =============================================================================
class Comp_Tank(flsb.Comp_Base):  # pylint: disable=invalid-name
  '''
  Cylindrical tank model with optional compressed headspace.

  Parameters:
    D: tank diameter (default in mm)
    H: tank height (default in m)
    fillheight: liquid height in the tank (default in m)
    closed: False=open to atmosphere, True=closed/compressible headspace
    Patm: atmospheric reference pressure (default in bar)
  '''
  _group: str = 'Equipment'
  _part: str = 'Tank'
  _prefix: str = 'Tk'
  _sign: float = +1.0

  def __init__(self, **kwargs: Any) -> None:
    args_in = fls.GetArgs(kwargs)
    self._atmospheric = args_in.getArg(
      'atmospheric',
      [
        fls.vFun.default(True),
        fls.vFun.istype(bool),
      ]
    )
    self._D = args_in.getArg(
      'D',
      [
        fls.vFun.istype(int, float, Quantity),
        fls.vFun.tounits(u.m),
        fls.vFun.islambda(lambda x: x.magnitude > 0.0, errmsg='D must be > 0'),
      ]
    )
    self._H = args_in.getArg(
      'H',
      [
        fls.vFun.istype(int, float, Quantity),
        fls.vFun.tounits(u.m),
        fls.vFun.islambda(lambda x: x.magnitude > 0.0, errmsg='H must be > 0'),
      ]
    )
    self._Dout = args_in.getArg(
      'Dout',
      [
        fls.vFun.istype(int, float, Quantity),
        fls.vFun.tounits(u.mm),
        fls.vFun.islambda(lambda x: x.magnitude > 0.0, errmsg='Dout must be > 0'),
      ]
    )
    self._level = args_in.getArg(
      'level',
      [
        fls.vFun.default(0.0 * u.m),
        fls.vFun.istype(int, float, Quantity),
        fls.vFun.tounits(u.m),
        fls.vFun.islambda(lambda x: x.magnitude >= 0.0, errmsg='level must be >= 0'),
        fls.vFun.islambda(lambda x: x <= self._H, errmsg='level must be <= H'),
      ]
    )
    self._Ptank = args_in.getArg(
      'Ptank',
      [
        fls.vFun.default(0*u.Pa),
        fls.vFun.istype(int, float, Quantity),
        fls.vFun.tounits(u.bar),
      ]
    )
    # Reference state for isothermal gas compression in closed mode.
    self._Vair_ref = self.Vair
    self._Ptank_ref = self._Ptank
    super().__init__(**args_in.restArgs())
    self._calcPressure()

  @property
  def atmospheric(self) -> bool:
    return self._atmospheric

  @atmospheric.setter
  def atmospheric(self, value: bool) -> None:
    self._atmospheric = value
    self._Vair_ref = self.Vair
    self._Ptank_ref = self._Ptank
    self._calcPressure()

  @property
  def D(self) -> Quantity:
    return self._D

  @property
  def H(self) -> Quantity:
    return self._H

  @property
  def Dout(self) -> Quantity:
    return self._Dout

  @property
  def level(self) -> Quantity:
    return self._level

  @level.setter
  def level(self, value: int | float | Quantity) -> None:
    new_level = fls.toUnits(value, u.m)
    if new_level.magnitude < 0.0:
      raise ValueError(f'level must be >= 0, got {new_level}')
    if new_level > self._H:
      raise ValueError(f'level must be <= H ({self._H:.4f~P}), got {new_level:.4f~P}')
    self._level = new_level
    self._calcPressure()

  @property
  def Vtot(self) -> Quantity:
    return (self._D * self._D * math.pi / 4 * self._H).to(u.m**3)

  @property
  def Vprod(self) -> Quantity:
    return (self._D * self._D * math.pi / 4 * self._level).to(u.m**3)

  @property
  def Vair(self) -> Quantity:
    return (self._D * self._D * math.pi / 4 * (self._H - self._level)).to(u.m**3)

  @property
  def Ptank(self) -> Quantity:
    '''Absolute pressure in the headspace.'''
    return self._Ptank

  def changeVolume(self, dV: int | float | Quantity) -> None:
    '''Modify liquid volume and update level accordingly.'''
    new_volume = self.Vprod + fls.toUnits(dV, u.m**3)
    if new_volume.magnitude < 0.0:
      new_volume = 0.0 * u.m**3
    elif new_volume > self.Vtot:
      new_volume = self.Vtot
    area = (self._D * self._D * math.pi / 4).to(u.m**2)
    self.level = new_volume / area

  def _calcPressure(self) -> None:
    if self._atmospheric:
      self._Ptank = 0 * u.bar
    else:
      # Isothermal compression around the chosen closed-tank reference state.
      Vair = self.Vair
      if Vair.magnitude <= 0.0:
        self._Ptank = float('inf') * u.bar
      else:
        p_atm = flsm.CTE_NP.to(u.bar)
        p_abs_ref = self._Ptank_ref + p_atm
        p_abs = p_abs_ref * self._Vair_ref / Vair
        self._Ptank = p_abs - p_atm

  def calcK(self, Q: Quantity, sense: int, pin: int=1, pout:int=2) -> float:  # pylint: disable=unused-argument
    '''Calculate exit loss coefficient.

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


  def calcH(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout: int=2) -> Quantity:  # pylint: disable=unused-argument
    '''Tank source head: hydrostatic head + gas gauge-pressure head.'''
    H_gas = fls.ptoH(self._Ptank, self.medium.rho)
    return (self.level + H_gas) * self._sign * sense

  def toString(self, detail: int=0) -> str:
    sdetail = detail // 10
    txt = super().toString(sdetail) + '\n'
    mode_str = 'Atmospheric' if self._atmospheric else 'Closed'
    txt += f' H:{self._H:.2f~P} '
    txt += f' D:{self._D:.1f~P} '
    txt += f' {mode_str} '
    txt += f' level:{self.level:.2f~P} '
    txt += f' Vprod:{self.Vprod:.3f~P} '
    txt += f' Vair:{self.Vair:.3f~P} '
    txt += f' Ptank:{self.Ptank:.3f~P} '
    txt += f'  H available: {self.calcH(0 * u.m**3 / u.h):.3f~P}'
    return txt

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  # Register dynamically via core registry.
  fls.registerComp('Tank', Comp_Tank, raiseerror=False)

  Htank = 20 * u.m
  Dtank = 3.8 * u.m
  Ltube = 50 * u.m
  Dtube = 70 *u.mm
  initlevel = 11 * u.m

  Tk1 = fls.getComp(comp='Tank', name='tank_open', atmospheric=True, H=Htank, D=Dtank, Dout=Dtube, level=initlevel)
  Tk2 = fls.getComp(comp='Tank', name='Tk2', atmospheric=False, H=Htank, D=Dtank, Dout=Dtube, level=initlevel)

  print('\nAtmospheric Tank')
  print(Tk1)
  Tk1.level = 17 * u.m
  print('\nAtmospheric Tank after level change')
  print(Tk1)
  print('\nClosed Tank')
  print(Tk2)
  Tk2.level = 17 * u.m
  print('\nClosed Tank after level change')
  print(Tk2)

  path1 = fls.getPath(
    name='path 1',
    components=[
      {'comp': fls.getComp(comp='Tube', L=Ltube, D=Dtube)},
      {'comp': fls.getComp(comp='Entrance', D=Dtube), 'sense': -1},
    ],
  )

  # ---------------------------------------------------------------------------
  # SIMULATION: drain both tanks via their paths until level change < threshold
  # ---------------------------------------------------------------------------
  deltaT = 30 * u.s
  step_max = 10000
  log_steps = 10
  print_steps = 50
  level_end = 1 * u.mm
  H_end = 1 * u.mm
  Q_end = 0.1 * u.m**3 / u.h
  end1 = False
  end2 = False

  H_Tk1 = Tk1.calcH(0.0 * u.m)
  H_Tk2 = Tk2.calcH(0.0 * u.m)
  wpt1 = fls.WpointDyn(s1=Tk1, s2=path1)
  wpt2 = fls.WpointDyn(s1=Tk2, s2=path1)
  step = 0
  X = [0]
  Y1_lvl = [Tk1.level.magnitude]
  Y1_P = [Tk1.Ptank.magnitude]
  Y1_Q = [wpt1.Q.magnitude]
  Y2_lvl = [Tk2.level.magnitude]
  Y2_P = [Tk2.Ptank.magnitude]
  Y2_Q = [wpt2.Q.magnitude]

  print(f'\n--- Simulation (dt={deltaT:.0f~P}, stop level < {level_end:.2f~P}) ---')
  print('                          Atmospheric                                     Closed')
  print('       t           level           P tank               H              Q            level           P tank               H              Q')
  print(f'{(step*deltaT).to(u.min):~P>8.1f}    {Tk1.level:~P>8.2f}     {Tk1.Ptank:~P>8.2f}     {wpt1.H:~P>8.3f}     {wpt1.Q:~P>8.2f}    {Tk2.level:~P>8.2f}     {Tk2.Ptank:~P>8.2f}     {wpt2.H:~P>8.3f}     {wpt2.Q:~P>8.2f}')
  while not(end1 and end2) and step <= step_max:
    if not end1:
      dV1 = (deltaT * wpt1.Q).to(u.m**3)
      Tk1.changeVolume(-dV1)
      #print(dV1,Tk1.level)
      wpt1.update()
      if Tk1.level <= level_end or wpt1.H <= H_end:
        end1 = True

    if not end2:
      dV2 = (deltaT * wpt2.Q).to(u.m**3)
      Tk2.changeVolume(-dV2)
      wpt2.update()
      if Tk2.level <= level_end or wpt2.H <= H_end:
        end2 = True

    step += 1
    if step % log_steps == 0:
      X.append((step*deltaT).to(u.min).magnitude)
      Y1_lvl.append(Tk1.level.magnitude)
      Y1_P.append(Tk1.Ptank.magnitude)
      Y1_Q.append(wpt1.Q.magnitude)
      Y2_lvl.append(Tk2.level.magnitude)
      Y2_P.append(Tk2.Ptank.magnitude)
      Y2_Q.append(wpt2.Q.magnitude)
    if step % print_steps == 0:
      print(f'{(step*deltaT).to(u.min):~P>8.1f}    {Tk1.level:~P>8.2f}     {Tk1.Ptank:~P>8.2f}     {wpt1.H:~P>8.3f}     {wpt1.Q:~P>8.2f}    {Tk2.level:~P>8.2f}     {Tk2.Ptank:~P>8.2f}     {wpt2.H:~P>8.3f}     {wpt2.Q:~P>8.2f}')

  fig = fls.PlotFigure(h=1000, w=2000, hw=60, nr=2, nc=2, title='Tank demo')
  fig.setExtra('title', size=33)
  # tank 1
  graph11 = fls.PlotGraph(fig, r=0, c=0, title='Atmospheric Tank')
  graph11.setXAxis(labeltxt='Time [min]')
  graph11.setYAxis(labeltxt='Level [m]', vmin=-0.0, vmax=20.0)
  graph11.setGrid(axis='both')
  curve11_1 = fls.PlotCurve(graph11, x=X, y=Y1_lvl, label='Level', color='tab:blue')
  graph12 = fls.PlotGraph(fig, r=1, c=0)
  graph12.setXAxis(labeltxt='Time [min]')
  graph12.setYAxis(labeltxt='Flow rate [m^3/s]')
  graph12.setYAxis2(labeltxt='Pressure [bar]', vmin=-1.0, vmax=9.0)
  graph12.setGrid(axis='both')
  graph12.setLegend(loc='best')
  curve12_1 = fls.PlotCurve(graph12, x=X, y=Y1_Q, label='Flow rate', color='tab:green')
  curve12_2 = fls.PlotCurve(graph12, x=X, y=Y1_P, axis='y2', label='Tank pressure', color='tab:red')

  # tank 2
  graph21 = fls.PlotGraph(fig, r=0, c=1, title='Closed Tank')
  graph21.setXAxis(labeltxt='Time [min]')
  graph21.setYAxis(labeltxt='Level [m]', vmin=-0.0, vmax=20.0)
  graph21.setGrid(axis='both')
  curve21_1 = fls.PlotCurve(graph21, x=X, y=Y2_lvl, label='Level', color='tab:blue')
  graph22 = fls.PlotGraph(fig, r=1, c=1)
  graph22.setXAxis(labeltxt='Time [min]')
  graph22.setYAxis(labeltxt='Flow rate [m^3/s]')
  graph22.setYAxis2(labeltxt='Pressure [bar]', vmin=-1.0, vmax=9.0)
  graph22.setGrid(axis='both')
  graph22.setLegend(loc='best')
  curve22_1 = fls.PlotCurve(graph22, x=X, y=Y2_Q, label='Flow rate', color='tab:green')
  curve22_2 = fls.PlotCurve(graph22, x=X, y=Y2_P, axis='y2', label='Tank pressure', color='tab:red')
  fig.show()
