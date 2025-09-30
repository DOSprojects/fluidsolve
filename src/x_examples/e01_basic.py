'''
    e01_basic

    Basic example comparing the `fluids` and `fluidsolve` calculations.
    For the fluidsolve calculations, two methods are shown.
    The first one instanciates component classes.
    The second one uses the builder class (factory pattern).

    See https://fluids.readthedocs.io/tutorial.html#pressure-drop-through-piping
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluids.units as fu
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':

  mu = 0.001 * u.Pa*u.s
  rho = 1000 * u.kg/u.m**3
  e = 0.01 * u.mm
  dia = 50 *u.mm
  dia2 = 25 *u.mm
  L = 15 * u.m

  medium = fls.Medium(name='test', mu=mu, rho=rho)
  v = 3 *u.m/u.s
  Q = fls.vtoQ(v, dia)
  print(f'v = {v}, Q = {Q}')
  print('----------\n')

  Re = fu.Reynolds(V=v, D=dia, rho=rho, mu=mu)
  fd = fu.friction_factor(Re, eD=e/dia)
  K_native = {}
  P_native = {}
  K_native['0'] = fu.K_from_f(fd=fd, L=L, D=dia)
  K_native['1'] = fu.entrance_sharp()
  K_native['2'] = fu.exit_normal()
  K_native['3'] = 2*fu.bend_miter(angle=30*u.degrees)
  K_native['4'] = fu.bend_rounded(Di=dia, angle=45*u.degrees, fd=fd)
  K_native['5'] = fu.contraction_sharp(Di1=dia, Di2=dia2)
  K_native['6'] = fu.diffuser_sharp(Di1=dia2, Di2=dia)
  K_native_T = sum(K_native.values())
  for key, value in K_native.items():
    P_native[key] = fu.dP_from_K(value, rho=rho, V=v)
  P_native_T = fu.dP_from_K(K_native_T, rho=rho, V=v)

  c_fls0 = {}
  K_fls0 = {}
  P_fls0 = {}
  c_fls0['0'] = fls.Comp_Tube(name='Tube',L=L, D=dia, e=e, medium=medium)
  c_fls0['1'] = fls.Comp_Entrance(name='Entrance', D=dia, use=1, e=e, medium=medium)
  c_fls0['2'] = fls.Comp_Entrance(name='Exit', D=dia, use=-1, e=e, medium=medium)
  c_fls0['3'] = fls.Comp_BendLong(name='BendLong', n=2, D=dia, A=30, e=e, medium=medium)
  c_fls0['4'] = fls.Comp_Bend(name='Bend', D=dia, A=45, R=5, e=e, medium=medium)
  c_fls0['5'] = fls.Comp_SharpReduction(name='Reduction', D1=dia, D2=dia2, e=e, use=1, medium=medium)
  c_fls0['6'] = fls.Comp_SharpReduction(name='Reduction', D1=dia2, D2=dia, e=e, use=-1, medium=medium)
  for key, value in c_fls0.items():
    K_fls0[key] = value.calcK(Q, 1)
    P_fls0[key] = value.calcP(Q, 1)
  K_fls0_T = sum(K_fls0.values())
  P_fls0_T = sum(P_fls0.values())

  c_fls1 = {}
  K_fls1 = {}
  P_fls1 = {}
  flsbuilder = fls.ComponentBuilder(medium=medium, e=e)
  c_fls1['0'] = flsbuilder.getComp(comp='Tube', L=L, D=dia)
  c_fls1['1'] = flsbuilder.getComp(comp='Entrance', D=dia, use=1)
  c_fls1['2'] = flsbuilder.getComp(comp='Entrance', D=dia, use=-1)
  c_fls1['3'] = flsbuilder.getComp(comp='BendLong', D=dia, A=30, n=2)
  c_fls1['4'] = flsbuilder.getComp(comp='Bend', D=dia, A=45, R=5)
  c_fls1['5'] = flsbuilder.getComp(comp='SharpReduction', D1=dia, D2=dia2, use=1)
  c_fls1['6'] = flsbuilder.getComp(comp='SharpReduction', D1=dia2, D2=dia, use=-1)
  for key, value in c_fls1.items():
    K_fls1[key] = value.calcK(Q, 1)
    P_fls1[key] = value.calcP(Q, 1)
  K_fls1_T = sum(K_fls1.values())
  P_fls1_T = sum(P_fls1.values())

  print('|     |  K native  |   K fls0   |   K fls1   |    P native    |     P fls0     |     P fls1     |')
  print('|-----|------------|------------|------------|----------------|----------------|----------------|')
  for i in [str(x) for x in range(7)]:
    print(f'|  {i}  | {K_native[i].magnitude:>10,.4f} | {K_fls0[i].magnitude:>10,.4f} | {K_fls1[i].magnitude:>10,.4f} | {P_native[i].to(u.bar):>10,.6f} | {P_fls0[i]:>10,.6f} | {P_fls1[i]:>10,.6f} |')
  print('|-----|------------|------------|------------|----------------|----------------|----------------|')
  print(f'| TOT | {K_native_T.magnitude:>10,.4f} | {K_fls0_T.magnitude:>10,.4f} | {K_fls1_T.magnitude:>10,.4f} | {P_native_T.to(u.bar):>10,.6f} | {P_fls0_T:>10,.6f} | {P_fls1_T:>10,.6f} |')
  print('|-----|------------|------------|------------|----------------|----------------|----------------|')
  print('p must be 0.379205 bar')