'''
  e12_plot.py

  Interactive Q-H plotting example with two independent pumps.
  Sliders modify system geometry and each pump speed separately.
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
pump1  = None
pump2  = None

# =============================================================================
# FUNCS
# =============================================================================
def fun1(value):
  '''Update system pipe length from slider input.'''
  system.getComp(0)['comp'].L = value
  plt.updateData()

def fun2(value):
  '''Update system pipe diameter from slider input.'''
  system.getComp(0)['comp'].D = value
  plt.updateData()

def fun3(value):
  '''Update first pump speed from slider input.'''
  pump1.speed = value
  plt.updateData()

def fun4(value):
  '''Update second pump speed from slider input.'''
  pump2.speed = value
  plt.updateData()

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  dataQH=fls.getPumpCurveDataText('''
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
  ''')
  fls.initFluidsolve(prefix_wpt='p')
  pump1 = fls.getComp(comp='PumpCentrifugal', dataQH=dataQH, impeller0=1, speed0=2900)
  pump2 = fls.getComp(comp='PumpCentrifugal', dataQH=dataQH, impeller0=1, speed0=2900, speed=1450)
  L = 315 * u.m
  dia  = 80
  dia2 = 40
  #
  system = fls.getPath(
    name='path 1',
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Entrance', D=dia)},
      {'comp': fls.getComp(comp='Entrance', D=dia), 'sense': -1},
      {'comp': fls.getComp(comp='BendLong', D=dia, A=30, n=2)},
      {'comp': fls.getComp(comp='Bend', D=dia, A=45, R=5)},
      {'comp': fls.getComp(comp='SharpReduction', D1=dia, D2=dia2)},
      {'comp': fls.getComp(comp='Reverse', reverse=fls.getComp(comp='SharpReduction', D1=dia, D2=dia2))},
    ],
  )
  #
  wpt1 = fls.getWpt(wpt='d', s1=pump1, s2= system)
  wpt2 = fls.getWpt(wpt='d', s1=pump2, s2= system)
  #
  print (f'Pump1: {pump1}')
  print (f'Pump2: {pump2}')
  print (f'Operating point: {wpt1}')
  print (f'Operating point: {wpt2}')
  #
  plt = fls.PlotQHcurve(
    pumps=[pump1, pump2],
    circuits=[system],
    wpoints=[wpt1, wpt2],
    title='Pumpcurve: 2 independent pumps',
    sliders=[
      dict(label='L (m)', vmin=100, vmax=800, vinit=system.getComp(0)['comp'].L.magnitude, fun=fun1),
      dict(label='D (mm)', vmin=40, vmax=100, vinit=system.getComp(0)['comp'].D.magnitude, fun=fun2),
      dict(label='P1 speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun3),
      dict(label='P2 speed (rpm)', vmin=1450, vmax=2900, vinit=1450, fun=fun4),
    ]
  )
  print(system.getComp(0)['comp'].L)
  print(system.getComp(0)['comp'].D)
  plt.show()
