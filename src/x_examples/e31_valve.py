'''
  e31_valve.py

  Network example featuring a three-way valve component.
  Illustrates setup and inspection of valve-centered circuits.
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import fluidsolve       as fls

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  cat = fls.Catalogue()
  pumprecs = cat.searchInLibrary(cat.findLibraries('APV'), 'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900')
  if len(pumprecs)>0:
    pr0 = pumprecs[0]
  else:
    raise ValueError('No pump found.')  

  flsbuilder = fls.ComponentBuilder()
  

  twvalve = flsbuilder.getComp(comp='Comp_Valve_3W', D=50)
  net1 = flsbuilder.getNetwork(
    name='net 1', 
    segments=[
      ['A', 'B', flsbuilder.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0']-200), 1],
      ['B', 'C', twvalve, 1],
      ['C', 'A', flsbuilder.getComp(comp='Tube', L=90, D=50), 1],
      ['B', 'D', twvalve, 2],
      ['D', 'A', flsbuilder.getComp(comp='Tube', L=115, D=50), 1],
    ],
  )

  '''dzvalve = flsbuilder.getComp(comp='Comp_Valve_ds', D=50)
  net2 = flsbuilder.getNetwork(
    name='net 2', 
    segments=[
      ['A', 'B', flsbuilder.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0']-200), 1],
      ['B', 'C', dzvalve, 1],
      ['C', 'D', flsbuilder.getComp(comp='Tube', L=90, D=50), 1],
      ['D', 'E', dzvalve, 2],
      ['E', 'A', flsbuilder.getComp(comp='Tube', L=115, D=50), 1],
    ],
  )'''
  net = net1
  print('Nodes: ', net.Nodes)
  print('Edges: ', net.Edges)
  print('Segments: ')
  for s in net.Segments:
    print(s)
  print('Adjacency: ', net.Adjacency)
  print('SpanningTree: ', net.SpanningTree)
  print('AllCycles: ', net.AllCycles)
  print('FundamentalCycles: ', net.FundamentalCycles)
  print('findShortestPath: ', net.findShortestPath('A', 'D'))
  print('\n\nfuncs')
  for i in net.Funcs['N']:
    print(i)

  for i in net.Funcs['L']:
    print('---------')
    for c in i:
      print('->', c)

  net1.calcNetwork(0.1)
  for i in net1.Result:
    print(i)

  '''net2.calcNetwork(1.0)
  for i in net2.Result:
    print(i)'''
