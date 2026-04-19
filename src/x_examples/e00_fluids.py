'''
  e00_fluids.py

  Basic example combining fluids, pint, and fluidsolve.
  Shows equivalent calculations with explicit engineering units.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
# pylint: disable=no-member
# Reason: fluids.units uses dynamic attributes that pylint can't detect
import fluids.core      as fc
import fluids.friction  as ff
import fluids.units     as fu # pylint: disable=no-name-in-module
import fluidsolve       as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  # some values
  Q = 30 *u.m**3/u.h
  v = 1.5 *u.m/u.s
  L = 100 *u.m
  dia  = 65 *u.mm # if no units defaults are presumed
  dia2 = 25       # if no units defaults are presumed
  #
  med = fls.Medium(prd='water')
  print(f'Water ({med.T:~P}): rho: {med.rho:~P} , mu: {med.mu:~P}')
  med.T = 95.0 * u.degC
  print(f'Water ({med.T:~P}): rho: {med.rho:~P} , mu: {med.mu:~P}')
  med.T = 20.0 * u.degC
  print(f'Water ({med.T:~P}): rho: {med.rho:~P} , mu: {med.mu:~P}')
  print('\nBerekeningen kunnen met of zonder units gedaan worden.')
  print('Dit bepaalt dan de gebruikte library:')
  print('  import fluids.core     as fc   voor gebruik zonder units.')
  print('  import fluids.units    as fu   voor gebruik met units.')
  print('Hieronder 1 berekening zonder units:')
  res = fc.Reynolds(D=0.065, V=1.5, rho=998.224, mu=0.001002058)
  print(f'Re: {res:.2f}')
  print('\nWij verkiezen om altijd met units te werken:')
  res = fu.Reynolds(D=dia, V=v, rho=med.rho, mu=med.mu)
  print(f'Re: {res:.2f~P}')
  res = fu.Prandtl(rho=med.rho, mu=med.mu, Cp=4200*u.J/u.kg/u.degK, k=0.6*u.W/u.m/u.degK)
  print(f'\nPrandtl: {res:.2f~P}')
  print('\nAlles omzetten naar loss coeff (kunnen gemakkelijk samengeteld worden).')
  res_K1 = fu.K_from_f(fd=0.018, L=L, D=dia).to_base_units()
  print(f'K_from_f: {res_K1:.2f~P}')
  res_K2 = fu.K_from_L_equiv(L_D=L/dia, fd=0.02).to_base_units() # L_D = length/dia
  print(f'K_from_L_equiv: {res_K2:.2f~P}')
  print('\nEens totale K gekend kan opvoerhoogte of drukval berekend worden.')
  res = fu.head_from_K(K=res_K1+res_K2, V=v*2)
  print(f'head_from_K: {res:.2f~P}')
  res = fu.dP_from_K(K=res_K1+res_K2, rho=med.rho, V=v*2).to(u.bar)
  print(f'dP_from_K: {res:.2f~P}')
  print('\nEen gekende K kan ook omgezet worden naar L/D ratio of equival L.')
  res = fu.L_from_K(K=6, fd=0.018, D=dia)
  print(f'L_from_K: {res:.2f~P}')
  res = fu.L_equiv_from_K(3.6, fd=0.02)
  print(f'L_equiv_from_K (=L/dia): {res:.2f~P}')
  print('\nOmrekeningen opvoerhoogte en drukval')
  res = fls.ptoH(p=1.5*u.bar, rho=med.rho).to_base_units()
  print(f'head_from_P: {res:.2f~P}')
  res = fls.Htop(H=15.0*u.m, rho=med.rho).to(u.bar)
  print(f'P_from_head: {res:.2f~P}')
  print('\nConverteren tussen dynamische and kinematische viscositeit: nu_mu_converter')
  res = fu.nu_mu_converter(rho=med.rho, nu=1.0E-6 * u.m**2/u.s)
  print(f'nu {1.0E-6 * u.m**2/u.s:~P} -> mu: {res:~P}')
  res = fu.nu_mu_converter(rho=med.rho, mu=med.mu)
  print(f'mu {med.mu:~P} -> nu: {res:~P}')
  print('\nZwaartekracht als functie van latitude en hoogte:')
  res = fu.gravity(latitude=55 *u.deg, H=0 *u.m)
  print(f'g= {res:.4f~P} voor lat: {55 *u.deg:~P} en H: {0 *u.m:~P}')
  res = fu.gravity(latitude=55 *u.deg, H=1000 *u.km)
  print(f'g= {res:.4f~P} voor lat: {55 *u.deg:~P} en H: {1000 *u.km:~P}')
  print('\nWrijvingsfactor:')
  epsilon = 1.5 *u.um # clean steel
  res = ff.friction_factor(Re=15000, eD=epsilon/dia)
  print(f'friction_factor: {res:.4f~P}')
  print('\nOvergang laminaire naar turbulente stroming flow is ogenblikkelijk geimplementeerd op Re=2040,')
  print('  d.i. 1 van de meest recente experemintele resultaten, nauwkeurig op +/- 10.')
  print('  Als Re in laminair regime debruiken we de gekende formule fd = 64/Re.')
  res = ff.friction_factor(Re=150)
  print(f'friction_factor: {res:.4f}')
  print('\nFriction factor in gebogen leidingen met friction_factor_curved.')
  print('De curved friction factor is toepasbaar voor helixen en spoelen, en in mindere mate voor gebogen leidingen.')
  res = ff.friction_factor_curved(Re=15000, Di=dia, Dc=2.5 *u.m, roughness=epsilon)
  print(f'friction_factor_curved: {res:.4f~P}')
  print('\nHet kritisch Reynolds getal voor gebogen leidingen is groter (en is functie van de buiging van de leiding')
  print('  Voorkeur berekeningsmethode (default) is de methode van Schmidt (1967): helical_transition_Re_Schmidt.')
  res = ff.helical_transition_Re_Schmidt(Di=dia, Dc=2.5 *u.m,)
  print(f'helical_transition_Re_Schmidt: {res:.0f~P}')
  print('\n')
