'''
  e50_plot.py

  Basic plotting-module example.
  Demonstrates curves, lines, annotations, and widgets.
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
  x1 = [x for x in range(0, 10)]
  y1 = [2+x*2 for x in range(0, 10)]
  lbl1 = [f"lbl{i}" for i in range(0, 10)]
  x2 = [x for x in range(5, 15)]
  y2 = [15*x**2 - x  for x in range(0, 10)]
  y3 = [5*x**3 - 40*x**2  for x in range(0, 10)]
  fig = fls.PlotFigure(h=400, w=800, hw=60, nr=2, nc=3, nrw=2, ncw=10, title='DETITLE')
  fig.setExtra('title', size=33)
  graph1 = fls.PlotGraph(fig, r=0, c=0, title='gr1')
  graph1.setGrid(axis='both')
  graph2 = fls.PlotGraph(fig, r=0, c=1, title='gr2')
  graph2.setExtra('title', size=33)
  graph3 = fls.PlotGraph(fig, r=1, c='0:2', title='gr3')
  graph3.setXAxis(vmin=-5, vmax=20, vstep=5, vmstep=3, labeltxt='x')
  graph3.setYAxis(vmin=-50, vmax=50, vstep=20, vmstep=2, labeltxt='y')
  graph3.setGrid(axis='both')
  graph4 = fls.PlotGraph(fig, r=':', c=2, title='gr4')
  curve1 = fls.PlotCurve(graph1, x=x1, y=y2)
  curve2 = fls.PlotCurve(graph2, x=x2, y=y3)
  curve3 = fls.PlotCurve(graph3, x=x1, y=y1)
  curve4 = fls.PlotCurve(graph4, x=x1, y=y1)
  btn1 : fls.PlotButton = fls.PlotButton(fig, r=0, c=8, label='BTN1', fun=lambda event: print('btn1'), color='lightblue', hovercolor='yellow')
  sld1 : fls.PlotSlider = fls.PlotSlider(fig, r=1, c='3:9', label='SLD1', vmin=0, vmax=100, fun=lambda val: print(f'sld1: {val}'), color='lightgreen')
  fig.show()
