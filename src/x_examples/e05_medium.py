'''
  e05_medium.py

  Medium example focused on property lookup and temperature effects.
  Demonstrates updates of rho and mu after changing temperature.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve       as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  #
  m_wtr = fls.Medium(prd='water')
  print(m_wtr.__dict__)
  print(f'Water ({m_wtr.T:~P}): rho: {m_wtr.rho:~P} , mu: {m_wtr.mu:~P}')
  m_wtr.T = 95.0 * u.degC
  print(f'Water ({m_wtr.T:~P}): rho: {m_wtr.rho:~P} , mu: {m_wtr.mu:~P}')
  #
  print('============')
  m_cust = fls.Medium(prd='water')
  print(f'Water ({m_cust.T:~P}): rho: {m_cust.rho:~P} , mu: {m_cust.mu:~P}')
  m_cust.T = 95.0 * u.degC
  print(f'Water ({m_cust.T:~P}): rho: {m_cust.rho:~P} , mu: {m_cust.mu:~P}')
