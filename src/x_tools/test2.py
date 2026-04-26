'''
test2.py

Exploratory scenario script using the current fluidsolve APIs.
Builds several representative serial circuits, evaluates operating points for
multiple pumps, and shows an interactive Q-H plot for one selected scenario.
'''
# =============================================================================
# IMPORTS
# =============================================================================
import textwrap

import fluidsolve as fls


# =============================================================================
# GLOBALS
# =============================================================================
u = fls.unitRegistry

pumpA = None
pumpB = None
pumpC = None
pumpD = None
plot = None


# =============================================================================
# HELPERS
# =============================================================================
def sync_pump_speeds(value):
  '''Synchronize all pump speeds from a single slider value.'''
  for pump in (pumpA, pumpB, pumpC, pumpD):
    if pump is not None:
      pump.speed = value
  if plot is not None:
    plot.updateData()

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  data_pA = textwrap.dedent('''
    0.016, 55.92814371257485
    2, 56.16766467065868
    4, 56.40718562874252
    6, 56.287425149700596
    8, 55.68862275449102
    10.016, 54.131736526946106
    12, 51.616766467065865
    14, 47.78443113772455
    15.984, 42.275449101796404
    18.080000000000002, 33.89221556886228
  ''')
  data_pB = textwrap.dedent('''
    0.05533199195171026, 63.32657200811359
    5.090543259557344, 63.488843813387426
    10.015090543259557, 63.488843813387426
    15.050301810865191, 63.00202839756592
    20.030181086519114, 62.10953346855984
    25.06539235412475, 60.892494929006084
    30.04527162977867, 59.350912778904664
    34.914486921529175, 57.5659229208925
    39.94969818913481, 55.45638945233266
    44.984909456740446, 53.18458417849899
    49.96478873239437, 50.42596348884381
    53.229376257545276, 48.39756592292089
  ''')
  data_pC = textwrap.dedent('''
    0.05533199195171026, 33.87423935091278
    5.035211267605634, 33.9553752535497
    9.959758551307848, 34.11764705882353
    15.050301810865191, 33.87423935091278
    19.974849094567404, 33.225152129817445
    25.06539235412475, 31.926977687626774
    30.04527162977867, 30.060851926977687
    34.914486921529175, 27.62677484787018
    40.83501006036217, 23.894523326572006
  ''')

  pumpA = fls.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText(data_pA), impeller0=200, speed0=2900)
  pumpB = fls.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText(data_pB), impeller0=210, speed0=2900)
  pumpC = fls.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText(data_pC), impeller0=155, speed0=2900)
  _cat = fls.Catalogue()
  _cat.loadAllData()
  _libs = _cat.findLibraries('APV')
  _results = _cat.searchInLibrary(_libs, 'T = centrifugal AND spec = "W+ 35/35" AND impeller0 = 165 AND speed0 = 2900')
  if not _results:
    raise ValueError('No matching pump found for spec="W+ 35/35".')
  _rec = _results[0]
  pumpD = fls.getComp(comp='PumpCentrifugal', dataQH=_rec['dataQH'], impeller0=_rec['impeller0'], speed0=_rec['speed0'])

  medium = fls.Medium(prd='water')
  H_static = 5 * u.m
  d_cip = 65 * u.mm
  n_bends = 20

  # (Q, specs) per scenario
  _pd = {
    'awb_single_steek':          (10 * u.m**3 / u.h, [
      ('Hstatic', dict(name='c stat',   Hs_pos=H_static)),
      ('Tube',    dict(name='cips_l',   L=30, D=d_cip)),
      ('Bend',    dict(name='cips_b',   n=n_bends, D=d_cip)),
      ('Tube',    dict(name='cipso_l',  L=10, D=50 * u.mm)),
      ('Bend',    dict(name='cipso_b',  n=5,  D=50 * u.mm)),
      ('Tube',    dict(name='prod_l',   L=10, D=32 * u.mm)),
      ('Bend',    dict(name='prod_b',   n=5,  D=32 * u.mm)),
    ]),
    'awb_awh_intermediate':      (10 * u.m**3 / u.h, [
      ('Hstatic', dict(name='c stat',   Hs_pos=H_static)),
      ('Tube',    dict(name='cipro_l_1', L=10, D=50 * u.mm)),
      ('Bend',    dict(name='cipro_b_1', n=5,  D=50 * u.mm)),
      ('Tube',    dict(name='cipso_l',  L=10, D=50 * u.mm)),
      ('Bend',    dict(name='cipso_b',  n=5,  D=50 * u.mm)),
      ('Tube',    dict(name='prod_l',   L=10, D=32 * u.mm)),
      ('Bend',    dict(name='prod_b',   n=5,  D=32 * u.mm)),
      ('Tube',    dict(name='cipro_l_2', L=10, D=50 * u.mm)),
      ('Bend',    dict(name='cipro_b_2', n=5,  D=50 * u.mm)),
    ]),
    'l_creme_samen':             (35 * u.m**3 / u.h, [
      ('Hstatic', dict(name='c stat',   Hs_pos=H_static)),
      ('Tube',    dict(name='cips_l',   L=50, D=d_cip)),
      ('Bend',    dict(name='cips_b',   n=n_bends, D=d_cip)),
      ('Tube',    dict(name='cipso_l',  L=5,  D=65 * u.mm)),
      ('Bend',    dict(name='cipso_b',  n=5,  D=65 * u.mm)),
      ('Tube',    dict(name='prod1_l',  L=12, D=80 * u.mm)),
      ('Bend',    dict(name='prod1_b',  n=5,  D=80 * u.mm)),
      ('Tube',    dict(name='prodr_l',  L=12, D=65 * u.mm)),
      ('Bend',    dict(name='prodr_b',  n=5,  D=65 * u.mm)),
      ('Tube',    dict(name='prod2_l',  L=12, D=80 * u.mm)),
      ('Bend',    dict(name='prod2_b',  n=5,  D=80 * u.mm)),
    ]),
    'stefan_samen_intermediate': (15 * u.m**3 / u.h, [
      ('Hstatic', dict(name='c stat',  Hs_pos=H_static)),
      ('Tube',    dict(name='prod1_l', L=15, D=50 * u.mm)),
      ('Bend',    dict(name='prod1_b', n=10, D=50 * u.mm)),
      ('Tube',    dict(name='cipr_l',  L=30, D=50 * u.mm)),
      ('Bend',    dict(name='cipr_b',  n=n_bends, D=d_cip)),
      ('Tube',    dict(name='prod2_l', L=30, D=50 * u.mm)),
      ('Bend',    dict(name='prod2_b', n=10, D=50 * u.mm)),
    ]),
  }
  flows    = {t: q for t, (q, _) in _pd.items()}
  circuits = {t: fls.getComp(comp='Serial', name=t, medium=medium, item=[fls.getComp(comp=c, medium=medium, **p) for c, p in s]) for t, (_, s) in _pd.items()}

  for topic, flow in flows.items():
    print(f'\n{topic}')
    print('-' * len(topic))
    for comp in circuits[topic].components:
      _parts = []
      if hasattr(comp, 'D'):
        _parts.append(f'Q2v={fls.Qtov(flow, comp.D):.2f~P}')
      _parts.append(f'H={comp.calcH(flow, 1):.2f~P}')
      _parts.append(f'P={comp.calcP(flow, 1):.2f~P}')
      print(comp)
      print('    ' + ' '.join(_parts))
    print(f'  Total: H={circuits[topic].calcH(flow, 1):.2f~P}, P={circuits[topic].calcP(flow, 1):.2f~P}')

  wps = {
    topic: {
      'A': fls.getWpt(wpt='d', name=f'{topic}:A', s1=pumpA, s2=circuit),
      'B': fls.getWpt(wpt='d', name=f'{topic}:B', s1=pumpB, s2=circuit),
      'C': fls.getWpt(wpt='d', name=f'{topic}:C', s1=pumpC, s2=circuit),
      'D': fls.getWpt(wpt='d', name=f'{topic}:D', s1=pumpD, s2=circuit),
    }
    for topic, circuit in circuits.items()
  }

  topic = 'awb_awh_intermediate'
  print(f'\nSelected scenario: {topic}')
  for key, pump in [('A', pumpA), ('B', pumpB), ('C', pumpC), ('D', pumpD)]:
    print(f'PUMP {key}: {pump}')
    print(f'Working point: {wps[topic][key]}')

  plot = fls.PlotQHcurve(
    pumps=[pumpA, pumpB, pumpC, pumpD],
    circuits=[circuits[topic]],
    wpoints=[wps[topic]['A'], wps[topic]['B'], wps[topic]['C'], wps[topic]['D']],
    Qmax=40,
    Hmax=80,
    title=f'Pump curves for scenario: {topic}',
    sliders=[
      dict(label='Speed (rpm)', vmin=500, vmax=3500, vinit=2900, fun=sync_pump_speeds),
    ],
  )
  plot.show()
