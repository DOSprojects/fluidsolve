'''
  a00_test.py

  Simple smoke-test style example.
  Demonstrates Medium instantiation and default properties.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluids
import fluidsolve as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  print('\nInstance:')
  m0 = fls.Medium()
  print(m0)
  print(m0.rho)
  print('\nDefault:')
  m1 = fls.getDefaultMedium()
  print(m1)
  print(m1.rho)
