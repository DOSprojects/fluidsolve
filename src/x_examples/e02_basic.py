'''
  e02_basic.py

  Basic factory-based example for path and component creation.
  Prints component-level and path-level hydraulic results.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# FUNCS
# =============================================================================
def PrintIt(comp, sense, flow_rate):
  '''Print component hydraulic details for a given flow and direction.'''
  print(f'{comp}')
  try:
    print(f'K={comp.calcK(flow_rate, sense).magnitude:.2f}')
  except Exception:
    print('K= not available')
  print(f'with Q={flow_rate:.2f~P} sense: {sense} : H={comp.calcH(flow_rate, sense):.2f~P} P={comp.calcP(flow_rate, sense):.2f~P}')
  print(f'with Q={flow_rate:.2f~P} sense: {-sense} : H={comp.calcH(flow_rate, -sense):.2f~P} P={comp.calcP(flow_rate, -sense):.2f~P}')
  print('-------------\n')

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':

  mu = 0.001 * u.Pa*u.s
  rho = 1000 * u.kg/u.m**3
  dia = 50 *u.mm
  dia2 = 25 *u.mm
  L = 15 * u.m

  medium = fls.Medium(name='test', mu=mu, rho=rho, k=fls.Medium(prd='water').k)
  v = 3 *u.m/u.s
  Q = fls.vtoQ(v, dia)
  #
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
  print('Flow to speed and vice versa (component 0):')
  print(f'v2Q met v={v:.2f~P}: {fls.vtoQ(v, path1.Components[0]['comp'].D):.2f~P}')
  print(f'Q2v met Q={Q:.2f~P}: {fls.Qtov(Q, path1.Components[0]['comp'].D):.2f~P}')
  print('-------------\n')
  print('Detail of all components:')
  for c in path1.Components:
    PrintIt(c['comp'], c['sense'], Q)
  print('Path:')
  PrintIt(path1, 1, Q)
  print ('Calculate profile (Q en H after every component, individual and incremental):')
  pts_indiv = path1.calcHprofile(Q, sense=1, incr=False)
  pts_incr = path1.calcHprofile(Q, sense=1, incr=True)
  for i, pt_indiv in enumerate(pts_indiv):
    print(f'{pt_indiv} \t\t {pts_incr[i]}')
  print('-------------\n')
