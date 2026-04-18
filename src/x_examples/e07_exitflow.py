'''
  e07_exitflow.py

  Example for exit-flow calculations.
  Compares fluids reference functions with fluidsolve helpers.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve   as fls
import fluids
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

#******************************************************************************
# GLOBALS
#******************************************************************************

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  D = 25.4 * u.mm
  H = 30 * u.m
  c = fls.getComp(comp='Entrance', D=D)
  Q = c.calcQ(H=H, sense=-1)
  print(f'\nFlow D={D:.2f~P}, dH={H:.2f~P} : {Q:.2f~P}')
  D = 25.4 * u.mm
  H = 10 * u.m
  c = fls.getComp(comp='Entrance', D=D)
  Q = c.calcQ(H=H, sense=-1)
  print(f'\nFlow D={D:.2f~P}, dH={H:.2f~P} : {Q:.2f~P}')
