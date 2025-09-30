'''
    e05_m_wtrium

    Example for the `m_wtrium` submodule.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve       as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  #
  m_wtr = fls.medium(prd='water')
  print(f'Water ({m_wtr.T:~P}): rho: {m_wtr.rho:~P} , mu: {m_wtr.mu:~P}')
  m_wtr.T = 95.0 * u.degC
  print(f'Water ({m_wtr.T:~P}): rho: {m_wtr.rho:~P} , mu: {m_wtr.mu:~P}')
  #
  print('============')
  m_cust = fls.medium(prd='water')
  print(f'Water ({m_cust.T:~P}): rho: {m_cust.rho:~P} , mu: {m_cust.mu:~P}')
  m_cust.T = 95.0 * u.degC
  print(f'Water ({m_cust.T:~P}): rho: {m_cust.rho:~P} , mu: {m_cust.mu:~P}')
