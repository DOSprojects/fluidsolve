'''
    e20_pump_serial

    Basic demo for an interactive QH-plot with a series of two identical pump curves and a system curve.
    For the pipe in the system, length and diameter can be modified.
    For the pumps, the impeller speed can be modified.
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
  pump1.speed = value
  pumpS.updateCurve()
  plt.updateData()

def fun4(value):
  pump2.speed = value
  pumpS.updateCurve()
  plt.updateData()

#******************************************************************************
# MAIN
#******************************************************************************
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
  flsbuilder = fls.ComponentBuilder(prefix_wpt='p')
  pump1 = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=dataQH, impeller0=1, speed0=2900)
  pump2 = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=dataQH, impeller0=1, speed0=2900, speed=2600)
  pumpS = flsbuilder.getComp(comp='PumpSerial', pumps=[pump1, pump2])
  L = 315 * u.m
  dia  = 65
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
  wpt = flsbuilder.getWpt(wpt='d', s1=pumpS, s2= system)
  #
  plt = fls.PlotQHcurve(
    pumps=[pump1, pump2, pumpS],
    circuits=[system],
    wpoints=[wpt],
    title=f'Pumpcurve: 2 serial pumps',
    sliders=[
      dict(label='L (m)', vmin=100, vmax=800, vinit=system.getItem(0).L.magnitude, fun=fun1),
      dict(label='D (mm)', vmin=25, vmax=65, vinit=system.getItem(0).D.magnitude, fun=fun2),
      dict(label='P1 speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun3),
      dict(label='P2 speed (rpm)', vmin=1450, vmax=2900, vinit=2600, fun=fun4),
    ]
  )
  plt.show()
