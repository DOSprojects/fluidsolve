'''
  e51_plot_simple.py

  Simple PlotSimple example.
  Demonstrates plotting user-provided x/y data on a single graph.

  This script opens multiple windows sequentially.
  Close each plot window to continue to the next example.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=invalid-name

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import numpy as np
from fluidsolve.plotext import PlotSimple

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  # 1) Absolutely minimal parameters: just x and y data.
  x_min = [0, 1, 2, 3, 4]
  y_min = [0, 1, 0, 1, 0]
  PlotSimple(x=x_min, y=y_min).show()

  # 2) Styled line with explicit axis labels and ranges.
  x_line = np.linspace(0.0, 10.0, 50).tolist()
  y_line = (np.sin(np.asarray(x_line)) * 5.0 + 10.0).tolist()
  PlotSimple(
    x=x_line,
    y=y_line,
    type='line',
    label='sin(x) scaled',
    color='tab:blue',
    marker='o',
    xlabel='x',
    ylabel='y',
    xmin=0.0,
    xmax=10.0,
    xstep=1.0,
    ymin=0.0,
    ymax=20.0,
    ystep=2.0,
    title='PlotSimple: styled line',
    h=400,
    w=900,
  ).show()

  # 3) Scatter example.
  x_scatter = np.linspace(0.0, 6.0, 20).tolist()
  y_scatter = (2.0 + 0.8 * np.asarray(x_scatter) + 0.4 * np.sin(3.0 * np.asarray(x_scatter))).tolist()
  PlotSimple(
    x=x_scatter,
    y=y_scatter,
    type='scatter',
    color='tab:orange',
    marker='x',
    xlabel='time',
    ylabel='value',
    title='PlotSimple: scatter',
    h=400,
    w=800,
  ).show()

  # 4) Bar example.
  PlotSimple(
    x=[1, 2, 3, 4],
    y=[4, 7, 3, 6],
    type='bar',
    color='tab:green',
    xlabel='category',
    ylabel='count',
    title='PlotSimple: bar',
    h=400,
    w=700,
  ).show()

  # 5) setData() workflow: initialize, replace data, then show.
  p_update = PlotSimple(x=[0, 1], y=[0, 1], title='PlotSimple: setData before show', h=350, w=800)
  p_update.setData(
    x=np.linspace(0.0, 2.0 * np.pi, 60).tolist(),
    y=np.cos(np.linspace(0.0, 2.0 * np.pi, 60)).tolist(),
  )
  p_update.show()
