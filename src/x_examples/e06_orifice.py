'''
  e06_orifice.py

  Example for orifice-related calculations.
  Demonstrates solving with different unknown parameters.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
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
  medium = fls.Medium(prd='water')
  print(medium.cprd)
  print('\nfls.calcOrifice(medium = medium, d=50, orifice=17.5, Pin=4, Pout=1)')
  Q = fls.calcOrifice(medium=medium, d=50, orifice=17.5, Pin=4, Pout=1)
  print(f'Q = {Q:.2f~P}')
  print('\nfls.calcOrifice(medium=medium, d=50, Q=10, Pin=4, Pout=1)')
  orifice = fls.calcOrifice(medium=medium, d=50, Q=10, Pin=4, Pout=1)
  print(f'orifice = {Q:.2f~P}')
  print('\nfls.calcOrifice(medium=medium, d=50, orifice=17.5, Q=10, Pout=1)')
  Pin = fls.calcOrifice(medium=medium, d=50, orifice=17.5, Q=10, Pout=1)
  print(f'Pin = {Pin:.2f~P}')
  print('\nfls.calcOrifice(medium = medium, d=50, orifice=17.5, Q=10, Pin=4)')
  Pout = fls.calcOrifice(medium=medium, d=50, orifice=17.5, Q=10, Pin=4)
  print(f'Pout = {Pout:.2f~P}')
