'''
    e21_pump_serial

    Basic demo for an interactive QH-plot with two different pump curves in parallel and a system curve.
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
  pumpP.updateCurve()
  plt.updateData()

def fun4(value):
  pump2.speed = value
  pumpP.updateCurve()
  plt.updateData()

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  cat = fls.Catalogue()
  cat.loadAllData()
  c = cat.findLibraries('APV')
  d1 = cat.searchInLibrary(c, 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  print(d1)
  d10 = d1[0]
  d2 = cat.searchInLibrary(c, 'T = centrifugal AND spec = "W+ 35/35" AND impeller0 = 165 AND speed0 = 2900')
  print(d2)
  d20 = d2[0]
  
  flsbuilder = fls.ComponentBuilder(prefix_wpt='p')
  pump1 = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=d10['dataQH'], impeller0=d10['impeller0'], speed0=d10['speed0'])
  pump2 = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=d20['dataQH'], impeller0=d20['impeller0'], speed0=d20['speed0'], speed = 2300)
  pumpP = flsbuilder.getComp(comp='PumpParallel', pumps=[pump1, pump2])
  L = 200 * u.m
  dia  = 80
  dia2 = 60
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
  wpt = flsbuilder.getWpt(wpt='d', s1=pumpP, s2= system)
  #
  plt = fls.PlotQHcurve(
    Qmax=80,
    pumps=[pump1, pump2, pumpP], 
    circuits=[system], 
    wpoints=[wpt], 
    title=f'Pumpcurve: 2 parallel pumps',
    sliders=[
      dict(label='L (m)', vmin=100, vmax=300, vinit=system.getItem(0).L.magnitude, fun=fun1),
      dict(label='D (mm)', vmin=50, vmax=100, vinit=system.getItem(0).D.magnitude, fun=fun2),
      dict(label='P1 speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun3),
      dict(label='P2 speed (rpm)', vmin=1450, vmax=2400, vinit=2300, fun=fun4),
    ]
  )
  plt.show()
