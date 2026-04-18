'''
  e22_pump_parallel.py

  Interactive Q-H plotting example for two different pumps in parallel.
  Sliders modify pipe dimensions and both pump speeds.
'''

#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

#******************************************************************************
# GLOBALS
#******************************************************************************
def fun1(value):
  '''Update system pipe length from slider input.'''
  system.getComp(0)['comp'].L = value
  plt.updateData()

def fun2(value):
  '''Update system pipe diameter from slider input.'''
  system.getComp(0)['comp'].D = value
  plt.updateData()

def fun3(value):
  '''Update first pump speed and refresh combined parallel curve.'''
  pump1.speed = value
  pumpP.updateCurve()
  plt.updateData()

def fun4(value):
  '''Update second pump speed and refresh combined parallel curve.'''
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
  
  fls.initFluidsolve(prefix_wpt='p')
  pump1 = fls.getComp(comp='PumpCentrifugal', dataQH=d10['dataQH'], impeller0=d10['impeller0'], speed0=d10['speed0'])
  pump2 = fls.getComp(comp='PumpCentrifugal', dataQH=d20['dataQH'], impeller0=d20['impeller0'], speed0=d20['speed0'], speed = 2300)
  pumpP = fls.getComp(comp='PumpParallel', pumps=[pump1, pump2])
  L = 200 * u.m
  dia  = 80
  dia2 = 60
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
  wpt = fls.getWpt(wpt='d', s1=pumpP, s2= system)
  #
  plt = fls.PlotQHcurve(
    Qmax=80,
    pumps=[pump1, pump2, pumpP], 
    circuits=[system], 
    wpoints=[wpt], 
    title=f'Pumpcurve: 2 parallel pumps',
    sliders=[
      dict(label='L (m)', vmin=100, vmax=300, vinit=system.getComp(0)['comp'].L.magnitude, fun=fun1),
      dict(label='D (mm)', vmin=50, vmax=100, vinit=system.getComp(0)['comp'].D.magnitude, fun=fun2),
      dict(label='P1 speed (rpm)', vmin=1450, vmax=2900, vinit=2900, fun=fun3),
      dict(label='P2 speed (rpm)', vmin=1450, vmax=2400, vinit=2300, fun=fun4),
    ]
  )
  plt.show()
