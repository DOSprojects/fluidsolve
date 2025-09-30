'''
    e02_basic

    Basic example with the builder class (factory pattern).

    See https://fluids.readthedocs.io/tutorial.html#pressure-drop-through-piping

'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity

#******************************************************************************
# FUNCS
#******************************************************************************
def PrintIt(comp, Q):
  print(f'{comp}')
  try:
    print(f'K={comp.calcK(Q, 1).magnitude:.2f}')
  except:
    print('K= not available')
  print(f'with Q={Q:.2f~P}: H={comp.calcH(Q, 1):.2f~P} P={comp.calcP(Q, 1):.2f~P}')
  print(f'with Q=-{Q:.2f~P}: H={comp.calcH(Q, -1):.2f~P} P={comp.calcP(Q, -1):.2f~P}')
  print('-------------\n')

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
  #
  flsbuilder = fls.ComponentBuilder(medium=medium, e=e)
  comps = []
  comps.append(flsbuilder.getComp(comp='Tube', L=L, D=dia))
  comps.append(flsbuilder.getComp(comp='Entrance', D=dia, use=1))
  comps.append(flsbuilder.getComp(comp='Entrance', D=dia, use=-1))
  comps.append(flsbuilder.getComp(comp='BendLong', D=dia, A=30, n=2))
  comps.append(flsbuilder.getComp(comp='Bend', D=dia, A=45, R=5))
  comps.append(flsbuilder.getComp(comp='SharpReduction', D1=dia, D2=dia2, use=1))
  comps.append(flsbuilder.getComp(comp='SharpReduction', D1=dia2, D2=dia, use=-1))
  comp_serial = flsbuilder.getComp(comp='Serial')
  for c in comps:
    comp_serial.addItem(c)
  #
  print(f'Flow to sped and vice versa (component 0):')
  print(f'v2Q met v={v:.2f~P}: {fls.vtoQ(v, comps[0].D):.2f~P}')
  print(f'Q2v met Q={Q:.2f~P}: {fls.Qtov(Q, comps[0].D):.2f~P}')
  print('-------------\n')
  print('Detail of all components:')
  for c in comps:
    PrintIt(c, Q)
  print('-------------\n')
  print('Total (serial) component:')
  PrintIt(comp_serial, Q)
  print('-------------\n')
  print (f'Calculate profile (Q en H after every component, indicidual and incremental):')
  pts_indiv = comp_serial.calcHprofile(Q, use=1, incr=False)
  pts_incr = comp_serial.calcHprofile(Q, use=1, incr=True)
  for i in range(len(pts_indiv)):
    print(f'{pts_indiv[i]} \t\t {pts_incr[i]}')
  print('-------------\n')
