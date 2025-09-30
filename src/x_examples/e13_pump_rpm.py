'''
    e13_pump_rpm

    Basic demo for a static QH-plot with one pump curves with different speeds and a system curve.
'''

#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity


#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':

  cat = fls.Catalogue()
  c = cat.findLibraries('APV')
  d1 = cat.searchInLibrary(c, 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  print(d1)
  d10 = d1[0]
  
  flsbuilder = fls.ComponentBuilder(prefix_wpt='p')
  pump1 = flsbuilder.getComp(comp='PumpCentrifugal', dataQH=d10['dataQH'], impeller0=d10['impeller0'], speed0=d10['speed0'])
  pump1.speed = 2500
  pump1.updateCurve()
  pump2 = pump1.clone()
  pump2.speed = 2000
  pump2.updateCurve()
  pump3 = pump1.clone()
  pump3.speed = 1500
  pump3.updateCurve()
  #
  system = flsbuilder.getComp(comp='Tube', L=350, D=80)
  #
  wpt1 = flsbuilder.getWpt(wpt='d', s1=pump1, s2=system)
  print(f'For pump (speed0={pump1.speed0:.0f~P} with speed {pump1.speed:.0f~P} : {wpt1}')
  wpt2 = flsbuilder.getWpt(wpt='d', s1=pump2, s2=system)
  print(f'For pump (speed0={pump2.speed0:.0f~P} with speed {pump2.speed:.0f~P} : {wpt2}')
  wpt3 = flsbuilder.getWpt(wpt='d', s1=pump3, s2=system)
  print(f'For pump (speed0={pump3.speed0:.0f~P} with speed {pump3.speed:.0f~P} : {wpt3}')
  #
  plt = fls.PlotQHcurve(
    pumps=[pump1, pump2, pump3], 
    circuits=[system], 
    wpoints=[wpt1, wpt2, wpt3], 
    title=f'Pumpcurve: 1 pump with different speeds (2500, 2000, 1500 rpm)',
    Qmax = 30,
    Hmax = 30,
  )
  plt.show()
