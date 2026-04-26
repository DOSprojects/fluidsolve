'''
  e30_basic.py

  Basic network-module example.
  Builds and solves representative network configurations.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve       as fls

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  #fls.initFluidsolve(prefix_wpt='p', prefix_comp='Comp_')
  cat = fls.Catalogue()
  pumprecs = cat.searchInLibrary(cat.findLibraries('APV'), 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  if len(pumprecs)>0:
    pr0 = pumprecs[0]
  else:
    raise ValueError('No pump found.')

  net1 = fls.getNetwork(
    name='net 1',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']-200)},
      {'nodes': ['B','A'], 'sense': 1, 'comp': fls.getComp(comp='Tube', L=100, D=50)},
    ],
  )
  net1.calcNetwork()
  print(net1.toString(detail=1))

  print('==========================================================================')

  net2 = fls.getNetwork(
    name='net 2',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'])},
      {'nodes': ['B','C'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['C','A'], 'comp': fls.getComp(comp='Tube', L=90, D=50)},
    ],
  )

  net2.calcNetwork()
  print(net2.toString(detail=1))

  print('==========================================================================')

  net3 = fls.getNetwork(
    name='net 3',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'])},
      {'nodes': ['B','C'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['C','D'], 'comp': fls.getComp(comp='Tube', L=90, D=50)},
      {'nodes': ['D','E'], 'comp': fls.getComp(comp='Tube', L=80, D=30)},
      {'nodes': ['F','E'], 'sense': +1, 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']-200)},
      {'nodes': ['C','F'], 'comp': fls.getComp(comp='Tube', L=75, D=50)},
      {'nodes': ['F','A'], 'comp': fls.getComp(comp='Tube', L=115, D=50)},
      #{nodes: ['F','A']'comp': fls.getComp(comp='Tube', L=115, D=50)},
      #{nodes: ['F','G', 'H']'comp': fls.getComp(comp='Comp_Valve_3W', D=50)},
      #{nodes: ['G','C','H','D']'comp': fls.getComp(comp='Comp_Valve_DS', D=50)},
    ],
  )
  net3.calcNetwork()
  print(net3.toString(detail=1))
