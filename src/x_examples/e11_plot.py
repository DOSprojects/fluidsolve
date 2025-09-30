'''
    e11_plot

    Basic demo for an interactive QH-plot with a pump curve and a system curve.
    For the pipe in the system, length and diameter can be modified.
    For the pump, the impeller speed can be modified.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity

#******************************************************************************
# GLOBALS
#******************************************************************************
def fun1(value):
  system.getItem(0).L = value
  plt.updateData()

def fun2(value):
  system.getItem(0).D = value
  plt.updateData()

def fun3(value):
  pump.speed = value
  plt.updateData()

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  flsbuilder = fls.ComponentBuilder(prefix_wpt='p')
  pump = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText('''
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
  L = 315 * u.m
  dia  = 80
  dia2 = 40
  #
  system = flsbuilder.getComp(comp='Serial')
  system.addItem(flsbuilder.getComp(comp='Tube', L=L, D=dia))
  system.addItem(flsbuilder.getComp(comp='Entrance', D=dia, use=1))
  system.addItem(flsbuilder.getComp(comp='Entrance', D=dia, use=-1))
  system.addItem(flsbuilder.getComp(comp='BendLong', D=dia, A=30, n=2))
  system.addItem(flsbuilder.getComp(comp='Bend', D=dia, A=45, R=5))
  system.addItem(flsbuilder.getComp(comp='SharpReduction', D1=dia, D2=dia2, use=1))
  system.addItem(flsbuilder.getComp(comp='SharpReduction', D1=dia2, D2=dia, use=-1))
  #
  Q, H = fls.calcOperatingPoint(pump, system)
  swpt = flsbuilder.getWpt(wpt='s', Q=Q, H=H)
  dwpt = flsbuilder.getWpt(wpt='d', s1=pump, s2= system)
  spts = [
    fls.Wpoint(name='p1', Q=20, H=2.2),
    fls.Wpoint(name='p2', Q=20, H=6.4),
    fls.Wpoint(name='p3', Q=20, H=15.1),
  ]
  #
  print (f'Pump: {pump}')
  print (f'Operating point (static): {swpt}')
  print (f'Operating point (dynamic): {dwpt}')
  #
  plt = fls.PlotQHcurve(
    pumps=[pump],
    circuits=[system],
    spoints=spts,
    wpoints=[dwpt],
    title=f'Pumpcurve: 1 pump',
    sliders=[
      dict(label='L (m)', vmin=100, vmax=800, vinit=system.getItem(0).L.magnitude, fun=fun1),
      dict(label='D (mm)', vmin=40, vmax=100, vinit=system.getItem(0).D.magnitude, fun=fun2),
      dict(label='speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun3)
    ]
  )
  print(system.getItem(0).L)
  print(system.getItem(0).D)
  plt.show()
