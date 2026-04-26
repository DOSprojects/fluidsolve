The ``plotlib`` submodule
=========================

Functional Analysis
-------------------

**Purpose**

A Matplotlib wrapper that encapsulates figure/graph/widget creation into a composable object hierarchy,
eliminating boilerplate and providing a consistent API for all plots in fluidsolve.

Class Hierarchy & Relationships
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   PlotFigure
   ├── PlotGraph  (1..n, registered via addGraph)
   │   ├── PlotCurve       (1..n, addCurve)
   │   ├── PlotLine        (0..n, addVline / addHline)
   │   ├── PlotAnnotation  (0..n, addAnnotation)
   │   ├── PlotAxis        (0..4: x1, y1, x2, y2)
   │   ├── PlotGrid        (0..1)
   │   └── PlotLegend      (0..1)
   ├── PlotButton  (0..n, widget panel, addButton)
   └── PlotSlider  (0..n, widget panel, addSlider)

All child objects hold a ``weakref`` back to their parent to avoid reference cycles.

Classes
^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Class
     - Role
   * - ``PlotFigure``
     - Top-level container. Manages ``plt.figure``, ``GridSpec``, optional widget figure, Tk window, and toolbar.
       Orchestrates ``show()`` / ``update()`` / ``updateData()`` on all children.
   * - ``PlotGraph``
     - Wraps a single ``matplotlib.axes.Axes``. Positioned in the parent ``GridSpec`` by row/column (int or slice).
       Owns axes, curves, lines, annotations, axis config, grid, and legend.
   * - ``PlotCurve``
     - One data series: ``line``, ``scatter``, or ``bar``.
       Supports in-place data update (``set_xdata`` / ``set_ydata`` / ``set_offsets``) without rebuilding the artist.
   * - ``PlotLine``
     - Static horizontal or vertical reference line (``axhline`` / ``axvline``).
   * - ``PlotAxis``
     - Configures one of four axis positions (``x1``, ``y1``, ``x2``, ``y2``).
       Handles limits, tick spacing (``vstep`` / ``vmstep``), axis sharing, and labels.
       Secondary axes use ``twiny()`` / ``twinx()``.
   * - ``PlotAnnotation``
     - Batch text annotations over lists of (x, y, label) triples. Supports alternating offsets (``xtoggle`` / ``ytoggle``) for readability.
       Fully redrawn on ``updateData()``.
   * - ``PlotGrid``
     - Delegates to ``ax.grid()`` with configurable axis, color, linestyle, linewidth.
   * - ``PlotLegend``
     - Delegates to ``ax.legend()`` with location, title, font sizes, columns, and frame.
   * - ``PlotButton``
     - Matplotlib ``Button`` widget in the separate widget figure. Fires a user-supplied ``Callable`` on click.
   * - ``PlotSlider``
     - Matplotlib ``Slider`` widget with min/max/step/init. Fires a user-supplied ``Callable`` on change.

Key Design Patterns
^^^^^^^^^^^^^^^^^^^

- **Two-phase construction**: objects are configured first, then ``show()`` is called lazily (once) by ``prepareShow()``.
  A ``_prepare`` flag prevents double-building.
- **Validated kwargs**: all ``__init__`` parameters go through ``flsa.GetArgs`` / ``flsa.vFun`` validators (type checks, range checks, defaults, coercions).
- **``extra`` dict escape hatch**: every class accepts an ``extra={}`` kwarg that is merged into the underlying matplotlib call,
  allowing full pass-through of any matplotlib option without needing to expose it explicitly.
- **Update modes**: ``update()`` redraws data and re-applies axes/grid; ``updateData()`` updates data in-place only — faster for interactive refresh.
- **Widget panel**: buttons and sliders live in a second ``plt.figure`` (separate from the graph figure),
  embedded side-by-side in the same Tk window. The widget panel is created when either buttons or sliders are registered.

----

.. automodule:: fluidsolve.plotlib
   :members:
   :undoc-members:
   :show-inheritance:

