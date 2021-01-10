from pokertrees import *
import random
from poker_env import PokerEnv

class OneSidePokerEnv(PokerEnv):
    def __init__(self, rules, player):
        PokerEnv.__init__(self, rules)
        self.player = player
        self.opp_strategies = [ {} for _ in range(self.rules.players)]

    def reset(self):
        self.cfr()
        self.root = self.tree.root.children[0]
        self.root = self.skip_opp_node(self.root)
        if (type(self.root) is TerminalNode):
          raise Exception('Terminal node exists at the top of game tree. Something is wrong.')
          
        infoset, valid_actions = self.node_observation(self.root)
        return self.root.player, infoset, valid_actions, 0, False

    def step(self, action):
        self.root = self.root.get_child(action)
        self.root = self.skip_opp_node(self.root)
        if type(self.root) is TerminalNode:
            # return self.cfr_terminal_node(root, reachprobs, sampleprobs)
            # set terminal utility
            payoffs = [0 for _ in range(self.rules.players)]
            for hands,winnings in list(self.root.payoffs.items()):
                if not self.terminal_match(hands):
                    continue
                for player in range(self.rules.players):
                    # prob = 1.0
                    # for opp,hc in enumerate(hands):
                    #     if opp != player:
                    #         prob *= reachprobs[opp]
                    # payoffs[player] = prob * winnings[player] / sampleprobs
                    payoffs[player] = winnings[player]

            return (None, None, None, payoffs, True)

        infoset, valid_actions = self.node_observation(self.root)
        return self.root.player, infoset, valid_actions, 0, False

    def skip_opp_node(self, root):
        while True:
            if type(root) is HolecardChanceNode:
                assert(len(root.children) == 1)
                root = root.children[0]
                continue
            if type(root) is BoardcardChanceNode:
                root = random.choice(root.children)
                continue
            if (type(root) is ActionNode and root.player is not self.player):
                infoset, valid_actions = self.node_observation(root)
                opp_action = None
                if infoset not in self.opp_strategies[root.player]:
                  opp_action = random.choice(valid_actions)
                else:
                  opp_action = self.opp_strategies[root.player][infoset]
                root = root.get_child(opp_action)
                continue
            else:
                break
          
        return root
      
    def set_opp_strategies(self, strategies):
      self.opp_strategies = strategies