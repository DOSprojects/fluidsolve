'''
  e10_plot.py

  Static Q-H plotting example.
  Displays one pump curve together with one system curve.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

#******************************************************************************
# FUNCS
#******************************************************************************
def fun1(value):
  '''Update system pipe length from slider input.'''
  system.getItem(0).L = value
  plt.update()

def fun2(value):
  '''Update pump speed from slider input.'''
  pump.speed = value
  plt.update()

#******************************************************************************
# MAIN
#******************************************************************************
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
      {'comp': fls.getComp(comp='Entrance', D=dia)},
      {'comp': fls.getComp(comp='Entrance', D=dia), 'sense': -1},
      {'comp': fls.getComp(comp='BendLong', D=dia, A=30, n=2)},
      {'comp': fls.getComp(comp='Bend', D=dia, A=45, R=5)},
      {'comp': fls.getComp(comp='SharpReduction', D1=dia, D2=dia2)},
      {'comp': fls.getComp(comp='Reverse', reverse=fls.getComp(comp='SharpReduction', D1=dia, D2=dia2))},
    ],
  )
  #
  wpt = fls.WpointDyn(s1=pump, s2=system)
  #
  print (f'Pump: {pump}')
  print (f'Operating point: {wpt}')
  for i in system.calcHprofile(Q):
    print (i)
  #
  plt = fls.PlotQHcurve(
    pumps=[pump],
    circuits=[system],
    wpoints=[wpt],
    title=f'Pumpcurve; Operating point: Q={wpt.Q:.1f~P}, H={wpt.H:.1f~P}',
  )
  plt.show()
