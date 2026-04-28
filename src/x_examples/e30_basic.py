r'''
e30_basic1.py

Basic network-module example.
Builds and solves representative network configurations.

Network 1: single pump and tube::

       +--pmp>--+
      /          \
      A            B
      \          /
       +--------+
         100m

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
  fls.initFluidsolve(prefix_wpt='p', prefix_comp='Comp_')
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
