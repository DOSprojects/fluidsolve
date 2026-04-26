'''
  e01_basic.py

  Basic comparison between fluids and fluidsolve pressure-drop calculations.
  Demonstrates both direct class construction and factory/builder usage.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position
# pyright: reportAttributeAccessIssue=false

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
from typing import Any
import fluids.units as fu_module
import fluidsolve   as fls
# UNITS
fu: Any   = fu_module
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':

  mu = 0.001 * u.Pa*u.s
  rho = 1000 * u.kg/u.m**3
  e = 0.01 * u.mm
  dia = 50 *u.mm
  dia2 = 25 *u.mm
  L = 15 * u.m

  v = 3 *u.m/u.s
  Q = fls.vtoQ(v, dia)
  print(f'v = {v}, Q = {Q}')
  print('----------\n')
  Re = fu.Reynolds(V=v, D=dia, rho=rho, mu=mu)
  fd = fu.friction_factor(Re, eD=e/dia)
  K_native = [
    fu.K_from_f(fd=fd, L=L, D=dia),
    fu.entrance_sharp(),
    fu.exit_normal(),
    2*fu.bend_miter(angle=30*u.degrees),
    fu.bend_rounded(Di=dia, angle=45*u.degrees, fd=fd),
    fu.contraction_sharp(Di1=dia, Di2=dia2),
    fu.diffuser_sharp(Di1=dia2, Di2=dia),
  ]
  P_native = [
    fu.dP_from_K(K, rho=rho, V=v)
    for K in K_native
  ]
  K_native_T = sum(K_native)
  P_native_T = fu.dP_from_K(K_native_T, rho=rho, V=v)

  fls.initFluidsolve(
    default_medium = fls.Medium(name='test', mu=mu, rho=rho, k=fls.Medium(prd='water').k),
    default_material = fls.Material(e=e),
  )
  path1 = fls.getPath(
    name='path 1',
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Entrance', D=dia)},
      {'comp': fls.getComp(comp='Entrance', D=dia), 'sense': -1},
      {'comp': fls.getComp(comp='BendLong', D=dia, A=30, n=2)},
      {'comp': fls.getComp(comp='Bend', D=dia, A=45, R=5)},
      {'comp': fls.getComp(comp='SharpReduction', D1=dia, D2=dia2)},
      {'comp': fls.getComp(comp='Reverse', reverse=fls.getComp(comp='SharpReduction', D1=dia, D2=dia2))},
    ],
  )
  K_fls = []
  P_fls = []
  H_fls = []
  for comp in path1.components:
    K_fls.append(comp['comp'].calcK(Q, comp['sense']))
    P_fls.append(comp['comp'].calcP(Q, comp['sense']))
    H_fls.append(comp['comp'].calcH(Q, comp['sense']))
  K_fls_T = sum(K_fls)
  P_fls_T = sum(P_fls)
  H_fls_T = sum(H_fls)

  print(fls.getDefaultMedium(), '\n')
  print(path1.toString(detail=1))
  print('|     |  K native  |   K fls    |    P native    |     P fls      |     H fls      |')
  print('|-----|------------|------------|----------------|----------------|----------------|')
  for i, k_native in enumerate(K_native):
    print(f'|  {i}  | {k_native.magnitude:>10,.4f} | {K_fls[i].magnitude:>10,.4f} | {P_native[i].to(u.bar):>10,.6f} | {P_fls[i]:>10,.6f} |  {H_fls[i]:>6,.2f}  |')
  print('|-----|------------|------------|----------------|----------------|----------------|')
  print(f'| TOT | {K_native_T.magnitude:>10,.4f} | {K_fls_T.magnitude:>10,.4f} | {P_native_T.to(u.bar):>10,.6f} | {P_fls_T:>10,.6f} |  {H_fls_T:>6,.2f}  |')
  print('|-----|------------|------------|----------------|----------------|----------------|')
  print('p must be 0.379205 bar')
