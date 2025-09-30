'''
    Example for orifice calculations
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

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  medium = fls.Medium()
  print('\nfls.calcOrifice(medium = medium, d=50, orifice=17.5, Pin=4, Pout=1)')
  Q = fls.calcOrifice(medium = medium, d=50, orifice=17.5, Pin=4, Pout=1)
  print(f'Q = {Q:.2f~P}')
  print('\nfls.calcOrifice(medium = medium, d=50, Q=10, Pin=4, Pout=1)')
  orifice = fls.calcOrifice(medium = medium, d=50, Q=10, Pin=4, Pout=1)
  print(f'orifice = {Q:.2f~P}')
  print('\nfls.calcOrifice(medium = medium, d=50, orifice=17.5, Q=10, Pout=1)')
  Pin = fls.calcOrifice(medium = medium, d=50, orifice=17.5, Q=10, Pout=1)
  print(f'Pin = {Pin:.2f~P}')
  print('\nfls.calcOrifice(medium = medium, d=50, orifice=17.5, Q=10, Pin=4)')
  Pout = fls.calcOrifice(medium = medium, d=50, orifice=17.5, Q=10, Pin=4)
  print(f'Pout = {Pout:.2f~P}')
