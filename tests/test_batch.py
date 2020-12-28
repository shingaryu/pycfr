import sys
import os
sys.path.insert(0,os.path.realpath('.'))
from pokerstrategy import *
from pokergames import *
from pokercfr import *
from poker_env import PokerEnv
from one_side_poker_env import OneSidePokerEnv
from env_oscfr import *
from env_oscfr_with_sp import *

def near(val, expected, distance=0.0001):
    return val >= (expected - distance) and val <= (expected + distance)

print ''
print ''
print 'Testing Batch Outcome Sampling (OS) CFR'
print ''
print ''


print 'Computing NE for Kuhn poker'
kuhn = kuhn_rules()

env_both = PokerEnv(kuhn)
env_player = OneSidePokerEnv(kuhn, 0)
env_opp = OneSidePokerEnv(kuhn, 1)
cfr = EnvOSCFRWithSP(kuhn)

iterations_per_block = 10000
blocks = 100
for block in range(blocks):
    print 'Iterations: {0}'.format(block * iterations_per_block)
    # cfr.run(env_both, iterations_per_block)
    for _env in [env_player, env_opp]:
        cfr.run(_env, iterations_per_block)
        strt = cfr.fixed_strategy()
        env_player.set_opp_strategies(strt)
        env_opp.set_opp_strategies(strt)
    result = cfr.profile.best_response()
    print 'Best response EV: {0}'.format(result[1])
    print 'Total exploitability: {0}'.format(sum(result[1]))
print 'Done!'
print ''
