from pokertrees import PublicTree
from pokerstrategy import StrategyProfile, Strategy
from env_oscfr import EnvOSCFR

# Replicate StrategyProfile for best_response()
class EnvOSCFRWithSP(EnvOSCFR):
    def __init__(self, rules, exploration=0.4):
        EnvOSCFR.__init__(self, 2, 3, exploration)
        self.profile = StrategyProfile(rules, [Strategy(i) for i in range(rules.players)])
        self.current_profile = StrategyProfile(rules, [Strategy(i) for i in range(rules.players)])
        self.tree = PublicTree(rules)
        self.tree.build()
        for s in self.profile.strategies:
          s.build_default(self.tree) # fill in all infoset to avoid best_response() calculation fails

    def cfr_strategy_update(self, reachprobs, sampleprobs, infoset, player, valid_actions):
        strategy = EnvOSCFR.cfr_strategy_update(self, reachprobs, sampleprobs, infoset, player, valid_actions)
        self.current_profile.strategies[player].policy[infoset] = self.sampling_strategies[player][infoset]
        self.profile.strategies[player].policy[infoset] = self.average_strategies[player][infoset]
        return strategy
