'''
  a00_test.py

  Simple smoke-test style example.
  Demonstrates Medium instantiation and default properties.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve as fls
import fluids
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  print('\nInstance:')
  m0 = fls.Medium()
  print(m0)
  print(m0.rho)
  print('\nDefault:')
  m1 = fls.getDefaultMedium()
  print(m1)
  print(m1.rho)
