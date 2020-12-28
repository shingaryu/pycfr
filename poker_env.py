from pokertrees import *
import random

class PokerEnv(object):
    def __init__(self, rules):
        self.rules = rules
        self.tree = PublicTree(rules)
        self.tree.build()
        print 'Information sets: {0}'.format(len(self.tree.information_sets))

        self.root = None

    def cfr(self):
        # Sample all cards to be used
        holecards_per_player = sum([x.holecards for x in self.rules.roundinfo])
        boardcards_per_hand = sum([x.boardcards for x in self.rules.roundinfo])
        todeal = random.sample(self.rules.deck, boardcards_per_hand + holecards_per_player * self.rules.players)
        # Deal holecards
        self.holecards = [tuple(todeal[p*holecards_per_player:(p+1)*holecards_per_player]) for p in range(self.rules.players)]
        self.board = tuple(todeal[-boardcards_per_hand:])
        # Set the top card of the deck
        self.top_card = len(todeal) - boardcards_per_hand

    def terminal_match(self, hands):
        for p in range(self.rules.players):
            if not self.hcmatch(hands[p], p):
                return False
        return True

    def hcmatch(self, hc, player):
        # Checks if this hand is isomorphic to the sampled hand
        sampled = self.holecards[player][:len(hc)]
        for c in hc:
            if c not in sampled:
                return False
        return True

    def boardmatch(self, num_dealt, node):
        # Checks if this node is a match for the sampled board card(s)
        for next_card in range(0, len(node.board)):
            if self.board[next_card] not in node.board:
                return False
        return True

    # def equal_probs(self, root):
    #     total_actions = len(root.children)
    #     probs = [0,0,0]
    #     if root.fold_action:
    #         probs[FOLD] = 1.0 / total_actions
    #     if root.call_action:
    #         probs[CALL] = 1.0 / total_actions
    #     if root.raise_action:
    #         probs[RAISE] = 1.0 / total_actions
    #     return probs

    def reset(self):
        self.cfr()
        self.root = root = self.tree.root.children[0]

        hc = self.holecards[root.player][0:len(root.holecards[root.player])]
        infoset = self.rules.infoset_format(root.player, hc, root.board, root.bet_history)
        valid_actions = [i for i in range(3) if root.valid(i)]

        return root.player, infoset, valid_actions, 0, False

    def step(self, action):
        self.root = root = self.root.get_child(action)

        while True:
            if type(root) is TerminalNode:
                # return self.cfr_terminal_node(root, reachprobs, sampleprobs)
                # set terminal utility
                payoffs = [0 for _ in range(self.rules.players)]
                for hands,winnings in root.payoffs.items():
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

            if type(root) is HolecardChanceNode:
                assert(len(root.children) == 1)
                root = root.children[0]
                continue
            if type(root) is BoardcardChanceNode:
                root = random.choice(root.children)
                continue
            else:
                break

        hc = self.holecards[root.player][0:len(root.holecards[root.player])]
        infoset = self.rules.infoset_format(root.player, hc, root.board, root.bet_history)
        valid_actions = [i for i in range(3) if root.valid(i)]

        return root.player, infoset, valid_actions, 0, False

class OneSidePokerEnv(PokerEnv):
    def __init__(self, rules, player):
        self.rules = rules
        self.tree = PublicTree(rules)
        self.tree.build()
        self.player = player
        print 'Information sets: {0}'.format(len(self.tree.information_sets))

        self.root = None
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
            for hands,winnings in self.root.payoffs.items():
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
    
    def node_observation(self, root):
        hc = self.holecards[root.player][0:len(root.holecards[root.player])]
        infoset = self.rules.infoset_format(root.player, hc, root.board, root.bet_history)
        valid_actions = [i for i in range(3) if root.valid(i)]
        return infoset, valid_actions

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