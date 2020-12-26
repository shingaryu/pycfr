import sys
import os
sys.path.insert(0,os.path.realpath('.'))
from pokerstrategy import *
from pokergames import *
from pokercfr import *
from pokercfr_batch import *

def near(val, expected, distance=0.0001):
    return val >= (expected - distance) and val <= (expected + distance)

print ''
print ''
print 'Testing Batch Outcome Sampling (OS) CFR'
print ''
print ''


print 'Computing NE for Kuhn poker'
kuhn = kuhn_rules()

# cfr = OSCFRBatch(kuhn)
env = PokerEnv(kuhn)
cfr = BatchOSCFR(kuhn, env)

iterations_per_block = 10000
blocks = 100
for block in range(blocks):
    print 'Iterations: {0}'.format(block * iterations_per_block)
    cfr.run(iterations_per_block)
    result = cfr.profile.best_response()
    print 'Best response EV: {0}'.format(result[1])
    print 'Total exploitability: {0}'.format(sum(result[1]))
print 'Done!'
print ''
