'''
    e30_basic

    Basic example for the network module.

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
  
  net = flsbuilder.getNetwork(
    name='net 1', 
    segments=[
      ['A', 'B', flsbuilder.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0']-200)],
      ['B', 'C', flsbuilder.getComp(comp='Tube', L=100, D=50)],
      ['C', 'D', flsbuilder.getComp(comp='Tube', L=90, D=50)],
      ['D', 'E', flsbuilder.getComp(comp='Tube', L=80, D=30)],
      ['F', 'E', flsbuilder.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0']-500)],
      ['C', 'F', flsbuilder.getComp(comp='Tube', L=75, D=50)],
      ['F', 'A', flsbuilder.getComp(comp='Tube', L=115, D=50)],
    ],
  )
  '''
  print('Nodes: ', net.Nodes)
  print('Edges: ', net.Edges)
  print('Segments: ')
  for s in net.Segments:
    print(s)
  print('Adjacency: ', net.Adjacency)
  print('SpanningTree: ', net.SpanningTree)
  print('AllCycles: ', net.AllCycles)
  print('FundamentalCycles: ', net.FundamentalCycles)
  print('findShortestPath: ', net.findShortestPath('B', 'E'))
  print('\n\nfuncs')
  for i in net.Funcs['N']:
    print(i)

  for i in net.Funcs['L']:
    print('---------')
    for c in i:
      print('->', c)'''

  net.calcNetwork(1.0)
  for i in net.Result:
    print(i)

