# pylint: disable=anomalous-backslash-in-string
'''
  e31_basic2.py

  Basic network-module example.
  Builds and solves representative network configurations.

  Network 2: single pump and two tubes in parallel.
          A---pmp>---B
          |          |
          |          |100m
          |          |
          +----------C
                90m

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
