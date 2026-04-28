'''
  e35_valve.py

  Network example featuring a three-way valve component.
  Illustrates setup and inspection of valve-centered circuits.
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
  cat = fls.Catalogue()
  pumprecs = cat.searchInLibrary(cat.findLibraries('APV'), 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  if len(pumprecs)>0:
    pr0 = pumprecs[0]
  else:
    raise ValueError('No pump found.')

  valve1 = fls.getComp(comp='Valve_3W', D=50, state=1)
  net1 = fls.getNetwork(
    name='net 1',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']-200)},
      {'nodes': ['B','C','D'], 'comp': fls.getComp(comp='Valve_3W', D=50, state=1)},
      {'nodes': ['C','A'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['D','A'], 'comp': fls.getComp(comp='Tube', L=200, D=50)},
    ],
  )
  #print(net1.toString(detail=1))
  net1.calcNetwork()
  print('==========================================================================')
  print('Valve state 1: B->C open, B->D closed')
  print(net1.resultString())
  net1.components[1]['comp'].state = 2
  net1.calcNetwork()
  print('Valve state 2: B->C closed, B->D open')
  print(net1.resultString())
  print('==========================================================================')

  valve2 = fls.getComp(comp='Valve_DS', D=50, state=1)
  net2 = fls.getNetwork(
    name='net 2',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']-200)},
      {'nodes': ['B','C','E','D'], 'comp': fls.getComp(comp='Valve_DS', D=50, state=1)},
      {'nodes': ['C','D'], 'comp': fls.getComp(comp='Tube', L=200, D=50)},
      {'nodes': ['E','A'], 'comp': fls.getComp(comp='Tube', L=50, D=50)},
    ],
  )
  print(net2.toString(detail=1))
  net2.calcNetwork()
  print('==========================================================================')
  print('Valve state 1: closed')
  print(net1.resultString())
  net2.components[1]['comp'].state = 2
  net2.calcNetwork()
  print('Valve state 2: open')
  print(net1.resultString())
  print('==========================================================================')
