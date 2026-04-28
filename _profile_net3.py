import cProfile, pstats, io, sys, time
sys.path.insert(0, 'src')
import fluidsolve as fls

cat = fls.Catalogue()
pumprecs = cat.searchInLibrary(
    cat.findLibraries('APV'),
    'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900'
)
if not pumprecs:
    raise ValueError('No pump found.')
pr0 = pumprecs[0]

net3 = fls.getNetwork(
    name='net 3',
    components=[
        {'nodes': ['A','B'], 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']+100)},
        {'nodes': ['B','C'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
        {'nodes': ['C','D'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
        {'nodes': ['D','E'], 'sense': -1, 'comp': fls.getComp(comp='PumpCentrifugal', dataQH=pr0['dataQH'], impeller0=pr0['impeller0'], speed0=pr0['speed0'], speed=pr0['speed0']+100)},
        {'nodes': ['E','F'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
        {'nodes': ['C','F'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
        {'nodes': ['A','F'], 'comp': fls.getComp(comp='Tube', L=100, D=50)},
    ],
)

pr = cProfile.Profile()
t0 = time.perf_counter()
pr.enable()
result = net3.calcNetwork()
pr.disable()
t1 = time.perf_counter()

print(f'Total time : {t1-t0:.6f}s')
print(f'Result rows: {len(result)}')
print(f'First-row keys: {list(result[0].keys())}')

# Try to surface solver/nfev from result rows or network internals
solver_found = nfev_found = None
for item in result:
    for k, v in item.items():
        kl = k.lower()
        if 'solver' in kl:
            solver_found = v
        if 'nfev' in kl or 'fevals' in kl or 'func_eval' in kl:
            nfev_found = v

print(f'Solver (from result): {solver_found}')
print(f'nfev   (from result): {nfev_found}')

# Also check network attributes
for attr in ['_solver', '_nfev', '_lastSolve', 'lastSolve', 'solverResult', '_solveResult']:
    if hasattr(net3, attr):
        print(f'net3.{attr} = {getattr(net3, attr)}')

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(10)
print(s.getvalue())
