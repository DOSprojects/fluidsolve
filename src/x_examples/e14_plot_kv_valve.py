'''
  e14_plot_kv_valve.py

  Static Q-H plotting example.
  Displays one pump curve together with one system curve.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# GLOBALS
# =============================================================================
system = None
plt    = None
pump   = None

# =============================================================================
# FUNCS
# =============================================================================
def fun1(value):
  '''Update system pipe length from slider input.'''
  system.getComp(0)['comp'].L = value
  plt.updateData()

def fun2(value):
  '''Update pump speed from slider input.'''
  pump.speed = value
  plt.updateData()

def fun3(value):
  '''Update valve state.'''
  system.getComp(1)['comp'].state = value
  plt.updateData()

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  pump = fls.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText('''
    3.1843575418994416, 36.22969837587006
    5.027932960893855, 36.43851508120649
    9.944134078212288, 36.75174013921113
    14.916201117318435, 36.542923433874705
    19.94413407821229, 36.02088167053363
    25.083798882681563, 34.87238979118329
    29.88826815642458, 33.4106728538283
    34.91620111731844, 31.531322505800457
    40.055865921787706, 29.02552204176333
    45.083798882681556, 25.684454756380504
    48.826815642458094, 23.07424593967517
  '''), impeller0=1, speed0=2900)
  Q = 38.73 * u.m**3/u.h
  L = 315 * u.m
  dia  = 70
  dia2 = 40
  #
  system = fls.getPath(
    name='path 1',
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_Kv', D=dia, Kvs= 25, state=0.5)},
    ],
  )
  #
  wpt = fls.WpointDyn(s1=pump, s2=system)
  plt = fls.PlotQHcurve(
    pumps=[pump],
    circuits=[system],
    wpoints=[wpt],
    title='Pumpcurve and system curve with valve',
    ymax=50,
    sliders=[
      dict(label='L (m)', vmin=100, vmax=800, vinit=system.getComp(0)['comp'].L.magnitude, fun=fun1),
      dict(label='P speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun2),
      dict(label='V state', vmin=0.0, vmax=1.0, vstep=0.01, vinit=system.getComp(1)['comp'].state, fun=fun3),
    ]
  )
  plt.show()
