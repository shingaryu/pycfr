import sys
sys.path.append('D:\Koki\Documents\Python Scripts\pycfr')
import os
sys.path.insert(0,os.path.realpath('.'))
from pokerstrategy import *
from pokergames import *
from pokercfr import *
from poker_env import PokerEnv
from one_side_poker_env import OneSidePokerEnv
from env_oscfr import *
from env_oscfr_with_sp import *
from matpltlibtest import *

def near(val, expected, distance=0.0001):
    return val >= (expected - distance) and val <= (expected + distance)

print('')
print('')
print('Testing Batch Outcome Sampling (OS) CFR')
print('')
print('')


print('Computing NE for Kuhn poker')
kuhn = kuhn_rules()

env_both = PokerEnv(kuhn)
env_player = OneSidePokerEnv(kuhn, 0)
env_opp = OneSidePokerEnv(kuhn, 1)
# cfr = OutcomeSamplingCFR(kuhn)
cfr = EnvOSCFRWithSP(kuhn)

iterations_per_block = 100
blocks = 500
target_regrets = []
target_info = 'A:/:'
best_res_ev_0 = []
best_res_ev_1 = []
exploytabilities = []
for block in range(blocks):
    print('Iterations: {0}'.format(block * iterations_per_block))
    # cfr.run(iterations_per_block)
    cfr.run(env_both, iterations_per_block)
    for _env in [env_player, env_opp]:
        cfr.run(_env, iterations_per_block)
        strt = cfr.fixed_strategy()
        env_player.set_opp_strategies(strt)
        env_opp.set_opp_strategies(strt)
    target_regrets.append(cfr.counterfactual_regret[0][target_info][:])
    result = cfr.profile.best_response()
    best_res_ev_0.append(result[1][0])
    best_res_ev_1.append(result[1][1])
    exploytabilities.append(sum(result[1]))    
    print('Best response EV: {0}'.format(result[1]))
    print('Total exploitability: {0}'.format(sum(result[1])))
print('Done!')
print('')


x = [ iterations_per_block * b for b in range(blocks)]
num_y = 3
x_label = 'iterations'
y_list = [ [regrets[i] for regrets in target_regrets] for i in range(num_y) ]
y_legends = [ 'action {0}'.format(i) for i in range(num_y) ]
y_label = 'cfr'
plot_multiple_y(x, x_label, y_list, y_legends, y_label, f'infoset: {target_info}')

y_values = [best_res_ev_0, best_res_ev_1, exploytabilities]
y_values_legends = [ 'best response ev (0)', 'best response ev (1)', 'exploytabilities']
plot_multiple_y(x, x_label, y_values, y_values_legends, y_label, 'exploytabilities')