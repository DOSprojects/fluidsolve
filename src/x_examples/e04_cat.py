'''
    e04_cat.py

    Example for the catalogue subsystem.
    Shows library discovery and record filtering with query expressions.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve   as fls

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  cat = fls.Catalogue()
  cat.loadAllData()
  print('\n')
  print('Search Libraries')
  print('============')
  lib1 = cat.findLibraries()
  print(lib1)
  print('============')
  lib2 = cat.findLibraries('APV')
  print(lib2)
  print('============')
  lib3 = cat.findLibraries('appendage AND bend')
  print(lib3)
  print('============')
  lib4 = cat.findLibraries('appendage AND (bend OR BS-90) OR (DIN11852 AND BS-90)')
  print(lib4)
  print('============')
  lib5 = cat.findLibraries('appendage AND (bend AND BS-90)')
  print(lib5)
  print('============')
  print('\n')
  print('Search in Libraries')
  print('============')
  items1 = cat.searchInLibrary(lib5, 'OD < 20')
  print(items1)
  print('============')
  items2 = cat.searchInLibrary(lib5, 'WT >= 2 AND DN < 80')
  print(items2)
  print('============')
  items3 = cat.searchInLibrary(lib5, 'OD < 26 AND WT = 1.5')
  print(items3)
