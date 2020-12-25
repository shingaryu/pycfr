from pokertrees import *
from pokerstrategy import *
import random
from pokercfr import ChanceSamplingCFR

class OSCFRBatch(ChanceSamplingCFR):
    def __init__(self, rules, exploration=0.4):
        ChanceSamplingCFR.__init__(self, rules)
        self.exploration = exploration

    def run(self, num_iterations):
        for iteration in range(num_iterations):
            self.cfr()
            self.simulate_episode()
            self.iterations += 1

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


    def simulate_episode(self):
        root = self.tree.root
        terminalPayoffs = []
        reachprobs = [1 for _ in range(self.rules.players)]
        sampleprobs = 1.0
        histories = []
        while True:
            if type(root) is TerminalNode:
                # return self.cfr_terminal_node(root, reachprobs, sampleprobs)
                # set terminal utility
                payoffs = [0 for _ in range(self.rules.players)]
                for hands,winnings in root.payoffs.items():
                    if not self.terminal_match(hands):
                        continue
                    for player in range(self.rules.players):
                        prob = 1.0
                        for opp,hc in enumerate(hands):
                            if opp != player:
                                prob *= reachprobs[opp]
                        payoffs[player] = prob * winnings[player] / sampleprobs

                terminalPayoffs = payoffs
                break

            if type(root) is HolecardChanceNode:
                assert(len(root.children) == 1)
                root = root.children[0]
                continue
            if type(root) is BoardcardChanceNode:
                root = random.choice(root.children)
                continue                

            hc = self.holecards[root.player][0:len(root.holecards[root.player])]
            infoset = self.rules.infoset_format(root.player, hc, root.board, root.bet_history)
            equal_probs = self.equal_probs(root)
            strategy = self.cfr_strategy_update(reachprobs, sampleprobs, infoset, root.player, equal_probs)
            action_probs = strategy.probs(infoset)
            if random.random() < self.exploration:
                action = self.random_action(root)
            else:
                action = strategy.sample_action(infoset)
            reachprobs[root.player] *= action_probs[action]
            csp = self.exploration * (1.0 / len(root.children)) + (1.0 - self.exploration) * action_probs[action]
            sampleprobs *= csp

            histories.append({ "node": root, "action": action, "actionprob": action_probs[action]})

            root = root.get_child(action)

        # print 'simulation done'

        weakenedPayoffs = terminalPayoffs
        for history in reversed(histories):
            root = history["node"]
            ev = weakenedPayoffs[history["node"].player]
            action = history["action"]
            actionprob = history["actionprob"]
            hc = self.holecards[root.player][0:len(root.holecards[root.player])]
            infoset = self.rules.infoset_format(root.player, hc, root.board, root.bet_history)
            valid_actions = [i for i in range(3) if root.valid(i)]
            player = root.player
            self.cfr_regret_update(ev, action, actionprob, infoset, valid_actions, player)
            weakenedPayoffs[history["node"].player] *= actionprob


    def update_regrets(self, terminalUtility):
        pass

    def random_action(self, root):
        options = []
        if root.fold_action:
            options.append(FOLD)
        if root.call_action:
            options.append(CALL)
        if root.raise_action:
            options.append(RAISE)
        return random.choice(options)

    def cfr_strategy_update(self, reachprobs, sampleprobs, infoset, player, equal_probs):
        # Update the strategies and regrets for each infoset
        # Get the current CFR
        prev_cfr = self.counterfactual_regret[player][infoset]
        # Get the total positive CFR
        sumpos_cfr = float(sum([max(0,x) for x in prev_cfr]))
        if sumpos_cfr == 0:
            # Default strategy is equal probability
            probs = equal_probs
        else:
            # Use the strategy that's proportional to accumulated positive CFR
            probs = [max(0,x) / sumpos_cfr for x in prev_cfr]
        # Use the updated strategy as our current strategy
        self.current_profile.strategies[player].policy[infoset] = probs

        # Update the weighted policy probabilities (used to recover the average strategy)
        for i in range(3):
            self.action_reachprobs[player][infoset][i] += reachprobs[player] * probs[i] / sampleprobs
        if sum(self.action_reachprobs[player][infoset]) == 0:
            # Default strategy is equal weight
            self.profile.strategies[player].policy[infoset] = equal_probs
        else:
            # Recover the weighted average strategy
            self.profile.strategies[player].policy[infoset] = [self.action_reachprobs[player][infoset][i] / sum(self.action_reachprobs[player][infoset]) for i in range(3)]
        # Return and use the current CFR strategy

        return self.current_profile.strategies[player]

    def cfr_regret_update(self, ev, action, actionprob, infoset, valid_actions, player):
        for i in valid_actions:
            immediate_cfr = -ev * actionprob
            if action == i:
                immediate_cfr += ev
            self.counterfactual_regret[player][infoset][i] += immediate_cfr
