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
# MAIN
#******************************************************************************
if __name__ == '__main__':
  print('\nCopy of class definition:')
  m0 = fls.Medium
  print(m0)
  print(m0.rho)
  print('\nClass instance:')
  m1 = fls.Medium()
  print(m1)
  print(m1.rho)
