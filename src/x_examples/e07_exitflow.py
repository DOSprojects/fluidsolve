'''
    Example for calculating exit flow
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
import fluids
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity

#******************************************************************************
# GLOBALS
#******************************************************************************

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  flsbuilder = fls.ComponentBuilder()
  D = 25.4 * u.mm
  H = 30 * u.m
  c = flsbuilder.getComp(comp='Entrance', D=D, use=-1)
  Q = c.calcQ(H=H)
  print(f'\nFlow D={D:.2f~P}, dH={H:.2f~P} : {Q:.2f~P}')
  D = 25.4 * u.mm
  H = 10 * u.m
  c = flsbuilder.getComp(comp='Entrance', D=D, use=-1)
  Q = c.calcQ(H=H)
  print(f'\nFlow D={D:.2f~P}, dH={H:.2f~P} : {Q:.2f~P}')
