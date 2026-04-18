'''
  e03_serial.py

  Demonstrates serial and parallel composition components.
  Includes generic Parallel and the dedicated Parallel2 variant.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

#******************************************************************************
# FUNCS
#******************************************************************************
def PrintIt(comp, Q):
  '''Print component hydraulic details for a given flow.'''
  print(f'{comp}')
  try:
    print(f'K={comp.calcK(Q, 1).magnitude:.2f}')
  except:
    print('K= not available') 
  print(f'with Q={Q:.2f~P}: H={comp.calcH(Q, 1):.2f~P} P={comp.calcP(Q, 1):.2f~P}')

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  mu = 0.001 * u.Pa*u.s
  rho = 1000 * u.kg/u.m**3
  e = 0.01 * u.mm
  dia1 = 50 *u.mm
  dia2 = 25 *u.mm
  L1 = 15 * u.m
  L2 = 50 * u.m

  v = 3 *u.m/u.s
  Q = fls.vtoQ(v, dia1)
  #
  fls.initFluidsolve(
    default_medium = fls.Medium(name='test', mu=mu, rho=rho, k=fls.Medium(prd='water').k),
    default_material = fls.Material(e=e),
  )
  c0 = fls.getComp(comp='Tube', L=L1, D=dia1)
  c1 = fls.getComp(comp='Tube', L=L2, D=dia2)
  c2 = fls.getComp(comp='Tube', L=L2, D=dia2)
  comp_serial = fls.getComp(comp='Serial')
  comp_serial.addComp(c0)
  comp_serial.addComp(c1)
  comp_parallel = fls.getComp(comp='Parallel')
  comp_parallel.addComp(c0)
  comp_parallel.addComp(c1)
  comp_parallel.calcH(Q, 1)
  comp_parallel2 = fls.getComp(comp='Parallel2')
  comp_parallel2.addComp(c0)
  comp_parallel2.addComp(c1)
  #
  print('-------------\n')
  print('Detail of all components:')
  PrintIt(c0, Q)
  PrintIt(c1, Q)
  print('-------------\n')
  print('Total (serial) component:')
  PrintIt(comp_serial, Q)
  print (f'Calculate profile (Q en H after every item, individual and incremental):')
  pts_indiv = comp_serial.calcHprofile(Q, sense=1, incr=False)
  pts_incr = comp_serial.calcHprofile(Q, sense=1, incr=True)
  for i in range(len(pts_indiv)):
    print(f'{pts_indiv[i]} \t\t {pts_incr[i]}')
  print('-------------\n')
  print('Total (parallel) component:')
  PrintIt(comp_parallel, Q)
  print (f'Q en H for every item:')
  for i in range(len(comp_parallel.Components)):
    print(f'Component {comp_parallel.getComp(i).name}: Q={comp_parallel.getQ()[i]:.2f~P} H={comp_parallel.getH()[i]:.2f~P}')
  print('-------------\n')
  print('Total (parallel2) component:')
  PrintIt(comp_parallel2, Q)
  print (f'Q en H for every item:')
  print(f'Component {comp_parallel2.getComp(0).name}: Q={comp_parallel2.getQ()[0]:.2f~P} H={comp_parallel2.getH()[0]:.2f~P}')
  print(f'Component {comp_parallel2.getComp(1).name}: Q={comp_parallel2.getQ()[1]:.2f~P} H={comp_parallel2.getH()[1]:.2f~P}')
