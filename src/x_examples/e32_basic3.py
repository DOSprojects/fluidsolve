# pylint: disable=anomalous-backslash-in-string
'''
e32_basic3.py

Basic network-module example.
Builds and solves representative network configurations.

Network 3: two pumps and multiple tubes in a more complex configuration::

          50m        100m
      B----------C----------D
      ^          |          ^
      pmp        |100m     pmp
      |          |          |
      A----------F----------E  
          150m        100m

'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: enable=anomalous-backslash-in-string
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve       as fls

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  fls.initFluidsolve(prefix_wpt='p', prefix_comp='Comp_')
  cat = fls.Catalogue()
  pumprecs = cat.searchInLibrary(cat.findLibraries('APV'), 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  if len(pumprecs)>0:
    pr0 = pumprecs[0]
  else:
    raise ValueError('No pump found.')

  net3 = fls.getNetwork(
    name='net 3',
    components=[
      {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']+100)},
      {'nodes': ['B','C'], 'comp': fls.getComp(comp='Tube', L=50, D=50)},
      {'nodes': ['D','C'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['D','E'], 'sense': -1, 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']+100)},
      {'nodes': ['E','F'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['C','F'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
      {'nodes': ['F','A'], 'comp': fls.getComp(comp='Tube', L=150, D=50)},
    ],
  )
  net3.calcNetwork()
  print(net3.toString(detail=1))

  #print(net3.resultCandidatesString())
