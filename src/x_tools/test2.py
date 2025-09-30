'''
    basic demo
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************
import textwrap
# unit juggling
from pint import UnitRegistry
# actemium fluids lib
import fluidsolve as af

#******************************************************************************
# GLOBALS
#******************************************************************************
#******************************************************************************
# INTERACTIONS
#******************************************************************************

def fun1(value):
  pumpA.speed = value
  pumpA.updateCurve()
  pumpB.speed = value
  pumpB.updateCurve()
  pumpC.speed = value
  pumpC.updateCurve()
  pumpD.speed = value
  pumpD.updateCurve()
  plt.update()
#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  u = UnitRegistry()
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
  pumpA = af.PumpCentrifugal(T='centrifugal', vendor='APV', spec='W+ 50/8', din=50, dout=50, impeller0=200, rpm=2900, data=data_pA)

  data_pB = textwrap.dedent('''
    0.05533199195171026, 63.32657200811359
    5.090543259557344, 63.488843813387426
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
  pumpB = af.PumpCentrifugal(T='centrifugal', vendor='APV', spec='W+ 55/35', din=65, dout=40, impeller0=210, rpm=2900, data=data_pB)

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
  pumpC = af.PumpCentrifugal(T='centrifugal', vendor='APV', spec='W+ 55/35', din=65, dout=40, impeller0=155, rpm=2900, data=data_pC)

  pumpcat = af.PumpCatalogue()
  pumpsel_pD = pumpcat.getPumps(vendor='APV', spec='W+ 35/35', din=65, impeller0=165, rpm=2900)
  pumpD = af.PumpCentrifugal(**pumpsel_pD[0])

  medium = af.Medium(prd='water')
  H_statisch = 5 *u.m

  H_spball = 0 *u.m

  #
  d_cip = 65 *u.mm
  n_bochten_cip = 20
  #
  prj = {
    ###################################
    # awb of awh (apart)
    'awb_single_steek' : {
      'Q': 10 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=30, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=10, D=50 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=50 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=10, D=32 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=5, D=32 *u.mm, medium=medium),

        'prodr_l': af.C_Tube(name="prodr_l", L=10, D=50 *u.mm, medium=medium),
        'prodr_b': af.C_Bend(name="prodr_b", n=5, D=50 *u.mm, medium=medium),
      },
    },  
    'awb_single_retour' : {
      'Q': 10 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=10, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),

        'cipr_l': af.C_Tube(name="cipr_l", L=30, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),

      },
    },  
    ###################################
    # awb en awh samen
    'awb_awh_steek' : {
      'Q': 10 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=30, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=10, D=50 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=50 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=10, D=32 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=5, D=32 *u.mm, medium=medium),

        'prodr_l': af.C_Tube(name="prodr_l", L=10, D=50 *u.mm, medium=medium),
        'prodr_b': af.C_Bend(name="prodr_b", n=5, D=50 *u.mm, medium=medium),
      },
    },  
    'awb_awh_intermediate' : {
      'Q': 10 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=10, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=10, D=50 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=50 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=10, D=32 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=5, D=32 *u.mm, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=10, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),
      },
    },  
    'awb_awh_retour' : {
      'Q': 10 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=10, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),

        'cipr_l': af.C_Tube(name="cipr_l", L=30, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),

      },
    },  
    ###################################
    # lijn creme van foisonneur (apart)
    'l_creme_single' : {
      'Q': 35 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=50, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=5, D=65 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=65 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=12, D=80 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=5, D=80 *u.mm, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=12, D=65 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=65 *u.mm, medium=medium),

        'cipr_l': af.C_Tube(name="cipr_l", L=50, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),
      },
    },  
    ###################################
    # lijn creme van foisonneur (samen)
    'l_creme_samen' : {
      'Q': 35 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=50, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=5, D=65 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=65 *u.mm, medium=medium),

        'prod1_l': af.C_Tube(name="prod1_l", L=12, D=80 *u.mm, medium=medium),
        'prod1_b': af.C_Bend(name="prod1_b", n=5, D=80 *u.mm, medium=medium),

        'prodr_l': af.C_Tube(name="prodr_l", L=12, D=65 *u.mm, medium=medium),
        'prodr_b': af.C_Bend(name="prodr_b", n=5, D=65 *u.mm, medium=medium),

        'prod2_l': af.C_Tube(name="prod2_l", L=12, D=80 *u.mm, medium=medium),
        'prod2_b': af.C_Bend(name="prod2_b", n=5, D=80 *u.mm, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=12, D=65 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=65 *u.mm, medium=medium),

        'cipr_l': af.C_Tube(name="cipr_l", L=50, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=50 *u.mm, medium=medium),
      },
    },  
    ###################################
    # stefan->enrobeuse (apart)
    'stefan_single_steek' : {
      'Q': 15 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=50, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),
        'cips2_l': af.C_Tube(name="cips2_l", L=30, D=50 *u.mm, medium=medium),
        'cips2_b': af.C_Bend(name="cips2_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=5, D=50 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=50 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=30, D=50 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=10, D=50 *u.mm, medium=medium),

      },
    },  
    'stefan_single_retour' : {
      'Q': 15 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=15, D=50 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=10, D=50 *u.mm, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=30, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),

        'cipr2_l': af.C_Tube(name="cipr_l", L=30, D=d_cip, medium=medium),
        'cipr2_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),
        'cipr_l': af.C_Tube(name="cipr_l", L=50, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),

      },
    },  
    ###################################
    # stefan->enrobeuse (samen)
    'stefan_samen_steek' : {
      'Q': 15 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'cips_l': af.C_Tube(name="cips_l", L=50, D=d_cip, medium=medium),
        'cips_b': af.C_Bend(name="cips_b", n=n_bochten_cip, D=d_cip, medium=medium),
        'cips2_l': af.C_Tube(name="cips2_l", L=30, D=50 *u.mm, medium=medium),
        'cips2_b': af.C_Bend(name="cips2_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'cipso_l': af.C_Tube(name="cipso_l", L=5, D=50 *u.mm, medium=medium),
        'cipso_b': af.C_Bend(name="cipso_b", n=5, D=50 *u.mm, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=30, D=50 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=10, D=50 *u.mm, medium=medium),

      },
    },  
    'stefan_samen_intermediate' : {
      'Q': 15 *u.m**3/u.h,
      'comps' :{
        'spball': af.C_Static(name="spball", Hs=H_spball, D=50 *u.mm, medium=medium),

        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'prod1_l': af.C_Tube(name="prod1_l", L=15, D=50 *u.mm, medium=medium),
        'prod1_b': af.C_Bend(name="prod1_b", n=10, D=50 *u.mm, medium=medium),

        'cipr_l': af.C_Tube(name="cipr_l", L=30, D=50 *u.mm, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),

        'prod2_l': af.C_Tube(name="prod2_l", L=30, D=50 *u.mm, medium=medium),
        'prod2_b': af.C_Bend(name="prod2_b", n=10, D=50 *u.mm, medium=medium),

      },
    },  
    'stefan_samen_retour' : {
      'Q': 15 *u.m**3/u.h,
      'comps' :{
        'c0': af.C_Static(name="c stat", Hs=H_statisch, D=d_cip, medium=medium),

        'prod_l': af.C_Tube(name="prod_l", L=15, D=50 *u.mm, medium=medium),
        'prod_b': af.C_Bend(name="prod_b", n=10, D=50 *u.mm, medium=medium),

        'cipro_l': af.C_Tube(name="cipro_l", L=30, D=50 *u.mm, medium=medium),
        'cipro_b': af.C_Bend(name="cipro_b", n=5, D=50 *u.mm, medium=medium),

        'cipr2_l': af.C_Tube(name="cipr_l", L=30, D=d_cip, medium=medium),
        'cipr2_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),
        'cipr_l': af.C_Tube(name="cipr_l", L=50, D=d_cip, medium=medium),
        'cipr_b': af.C_Bend(name="cipr_b", n=n_bochten_cip, D=d_cip, medium=medium),

      },
    },  
    ###################################
  }
  #
  circuits = {}
  for topic, data in prj.items():
    circuits[topic] = af.C_Serial(medium=medium)
    for name, comp in data['comps'].items():
      circuits[topic].addComp(name, comp)
  #
  
  for topic, data in prj.items():
    for name, comp in data['comps'].items():
      print(f'{comp}')
      print(f'    with Q={data["Q"]:.2f~P}: Q2v: {af.Qtov(data["Q"], comp.D):.2f~P} H={comp.calcH(Q=data["Q"]):.2f~P} P={comp.calcP(Q=data["Q"]):.2f~P}')
    print (f'{topic} (Q={data["Q"]:.2f~P}): Htot: {circuits[topic].calcH(Q=data["Q"]):.2f~P}, ptot: {circuits[topic].calcP(Q=data["Q"]):.2f~P}')
    print ('- - - - - - - - - -')

  for topic, data in prj.items():
    print (f'{topic} (Q={data["Q"]:.2f~P}): Htot: {circuits[topic].calcH(Q=data["Q"]):.2f~P}, ptot: {circuits[topic].calcP(Q=data["Q"]):.2f~P}')
    print ('- - - - - - - - - -')

  # operating point
  wps = {}
  for topic, data in prj.items():
    wps[topic] = {}
    wps[topic]['A'] = af.WpointDyn(pump=pumpA, circuit=circuits[topic])
    wps[topic]['A'].name=topic+':A'
    wps[topic]['B'] = af.WpointDyn(pump=pumpB, circuit=circuits[topic])
    wps[topic]['B'].name=topic+':B'
    wps[topic]['C'] = af.WpointDyn(pump=pumpC, circuit=circuits[topic])
    wps[topic]['C'].name=topic+':C'
    wps[topic]['D'] = af.WpointDyn(pump=pumpD, circuit=circuits[topic])
    wps[topic]['D'].name=topic+':D'

  for topic, data in prj.items():
    if topic == 'awb_awh_intermediate':
      print (f'PUMP A: {pumpA}')
      print (f'werkpunt: {wps[topic]["A"]}')
      print (f'PUMP B: {pumpB}')
      print (f'werkpunt: {wps[topic]["B"]}')
      print (f'PUMP C: {pumpC}')
      print (f'werkpunt: {wps[topic]["C"]}')
      print (f'PUMP D: {pumpD}')
      print (f'werkpunt: {wps[topic]["D"]}')
      print ('- - - - - - - - - -')
      # grafiek
      plt = af.QHcurve(pumps=(pumpA, pumpD), circuits=circuits[topic], wpoints=(wps[topic]["A"], wps[topic]["D"]), Qmax=40, Hmax=80)
      plt.addResetInteraction()
      plt.addCircuitInteraction(fun1, 'speed', 500, 3500, 2900)
      plt.plot()
  #

