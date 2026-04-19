'''
  e08_wp.py

  Working-point example in the Q-H plane.
  Computes the operating point from a pump and a system path.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================
# pylint: disable=no-member,no-name-in-module,invalid-name,wrong-import-position

# =============================================================================
# EXTERNAL MODULE REFERENCES
# =============================================================================
import fluidsolve   as fls
# UNITS
u         = fls.unitRegistry
Quantity  = fls.Quantity  # type: ignore[misc]

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
  pump = fls.getComp(comp='PumpCentrifugal', dataQH=fls.getPumpCurveDataText('''
    3.1843575418994416, 36.22969837587006
    5.027932960893855, 36.43851508120649
    9.944134078212288, 36.75174013921113
    14.916201117318435, 36.542923433874705
    19.94413407821229, 36.02088167053363
    25.083798882681563, 34.87238979118329
    29.88826815642458, 33.4106728538283
    34.91620111731844, 31.531322505800457
    40.055865921787706, 29.02552204176333
    45.083798882681556, 25.684454756380504
    48.826815642458094, 23.07424593967517
  '''), impeller0=1, speed0=2900)
  L = 315 * u.m
  dia  = 40
  #
  system = fls.getComp(comp='Tube', L=L, D=dia)
  #
  wpt = fls.WpointDyn(s1=pump, s2=system)
  #
  print (f'Pump H: {pump.dataH}')
  print (f'Pump Q: {pump.dataQ}')
  print (f'Operating point: {wpt}')
