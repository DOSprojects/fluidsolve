'''
  e09_basic.py

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
def PrintIt(pts1, pts2, title1, title2):
  comp_w = 16
  h_w = 16
  print(f'{"Comp":<{comp_w}}{title1:>{h_w}}{title2:>{h_w}}')
  print(f'{"-" * comp_w}{"-" * h_w}{"-" * h_w}')
  n_rows = max(len(pts1), len(pts2))
  for i in range(n_rows):
    p1 = pts1[i] if i < len(pts1) else None
    p2 = pts2[i] if i < len(pts2) else None
    comp = p1.name if p1 is not None else (p2.name if p2 is not None else '')
    h1 = f'{p1.H.to(u.m).magnitude:.2f} m' if p1 is not None else ''
    h2 = f'{p2.H.to(u.m).magnitude:.2f} m' if p2 is not None else ''
    print(f'{comp:<{comp_w}}{h1:>{h_w}}{h2:>{h_w}}')
  print(f'{"-" * comp_w}{"-" * h_w}{"-" * h_w}\n')

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  dia = 80 *u.mm
  L = 20 * u.m
  Q = 40 * u.m**3/u.h
  # NR valve
  path1 = fls.getPath(
    name='path 1', 
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_NR', D=dia, state=1)},
    ],
  )
  path1_ptsA = path1.calcHprofile(Q)
  path1.getComp(1)['sense'] = -1
  path1_ptsB = path1.calcHprofile(Q)
  print(f'Path with non-return valve (Q = {Q:.2f~P}):')
  PrintIt(path1_ptsA, path1_ptsB, '--->', '<---')
  # on off valve
  path2 = fls.getPath(
    name='path 2', 
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_01', D=dia, state=1)},
    ],
  )
  path2_ptsA = path2.calcHprofile(Q)
  path2.getComp(1)['comp'].state = 0
  path2_ptsB = path2.calcHprofile(Q)
  print(f'Path with on-off valve (Q = {Q:.2f~P}):')
  PrintIt(path2_ptsA, path2_ptsB, 'V on', 'V off')
  # CV valve
  path3 = fls.getPath(
    name='path 3', 
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_CV', D=dia, state=6)},
    ],
  )
  path3_ptsA = path3.calcHprofile(Q)
  path3.getComp(1)['comp'].state = 12
  path3_ptsB = path3.calcHprofile(Q)
  print(f'Path with CV valve (Q = {Q:.2f~P}):')
  PrintIt(path3_ptsA, path3_ptsB, 'CV=2', 'CV=4')
  # 3W valve
  path4 = fls.getPath(
    name='path 4', 
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_3W', D=dia, state=1), 'pin':1, 'pout':2},
    ],
  )
  path4_ptsA = path4.calcHprofile(Q)
  path4.getComp(1)['comp'].state = 2
  path4_ptsB = path4.calcHprofile(Q)
  print(f'Path with 3W valve (port 1-2) (Q = {Q:.2f~P}):')
  PrintIt(path4_ptsA, path4_ptsB, 'rust', 'actief')
  # change to port 1-3
  path4.getComp(1)['pout'] = 3
  path4.getComp(1)['comp'].state = 1
  path4_ptsC = path4.calcHprofile(Q)
  path4.getComp(1)['comp'].state = 2
  path4_ptsD = path4.calcHprofile(Q)
  print(f'Path with 3W valve (port 1-3) (Q = {Q:.2f~P}):')
  PrintIt(path4_ptsC, path4_ptsD, 'rust', 'actief')
  # change to port 2-3
  path4.getComp(1)['pin'] = 2
  path4.getComp(1)['comp'].state = 1
  path4_ptsE = path4.calcHprofile(Q)
  path4.getComp(1)['comp'].state = 2
  path4_ptsF = path4.calcHprofile(Q)
  print(f'Path with 3W valve (port 2-3) (Q = {Q:.2f~P}):')
  PrintIt(path4_ptsE, path4_ptsF, 'rust', 'actief')
  # DS valve
  path5 = fls.getPath(
    name='path 5', 
    components=[
      {'comp': fls.getComp(comp='Tube', L=L, D=dia)},
      {'comp': fls.getComp(comp='Valve_DS', D=dia, state=1), 'pin':1, 'pout':3},
    ],
  )
  path5_ptsA = path5.calcHprofile(Q)
  path5.getComp(1)['comp'].state = 2
  path5_ptsB = path5.calcHprofile(Q)
  print(f'Path with double seat valve (Q = {Q:.2f~P}):')
  PrintIt(path5_ptsA, path5_ptsB, 'State 1', 'State 2')
