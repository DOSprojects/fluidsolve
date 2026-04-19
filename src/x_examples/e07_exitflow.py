'''
  e07_exitflow.py

  Example for exit-flow calculations.
  Compares fluids reference functions with fluidsolve helpers.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluids
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# GLOBALS
# =============================================================================
# =============================================================================
# MAIN
# =============================================================================
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
