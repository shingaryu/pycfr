import random

class EnvOSCFR(object):
    def __init__(self, n_players, n_actions, exploration=0.4):
        self.sampling_strategies = [ {} for _ in range(n_players)]
        self.average_strategies = [ {} for _ in range(n_players)]        
        self.iterations = 0
        self.counterfactual_regret = []
        self.action_reachprobs = []
        self.exploration = exploration
        self.counterfactual_regret = [ {} for _ in range(n_players)]
        self.action_reachprobs = [ {} for _ in range(n_players)]
        self.n_players = n_players
        self.num_of_actions = n_actions

    def run(self, env, num_iterations):
        for _ in range(num_iterations):
            self.simulate_episode(env)
            self.iterations += 1

    def sample_action(self, strategy, infoset):
        probs = strategy[infoset]
        val = random.random()
        total = 0
        for i,p in enumerate(probs):
            total += p
            if p > 0 and val <= total:
                return i
        raise Exception('Invalid probability distribution. Infoset: {0} Probs: {1}'.format(infoset, probs))

    def simulate_episode(self, env):
        player, infoset, valid_actions, reward, isFinished = env.reset()
        terminalPayoffs = []
        reachprobs = [1 for _ in range(self.n_players)]
        sampleprobs = 1.0
        histories = []
        while True:
            strategy = self.cfr_strategy_update(reachprobs, sampleprobs, infoset, player, valid_actions)
            action_probs = strategy[infoset]
            if random.random() < self.exploration:
                action = random.choice(valid_actions)
            else:
                action = self.sample_action(strategy, infoset)
            reachprobs[player] *= action_probs[action]
            csp = self.exploration * (1.0 / len(valid_actions)) + (1.0 - self.exploration) * action_probs[action]
            sampleprobs *= csp

            histories.append((player, infoset, valid_actions, action, action_probs[action]))

            player, infoset, valid_actions, reward, isFinished = env.step(action)
            if (isFinished):
                terminalPayoffs = reward

                for player in range(self.n_players):
                    prob = 1.0
                    for i in range(self.n_players):
                        if i != player:
                            prob *= reachprobs[i]
                    terminalPayoffs[player] = prob * reward[player] / sampleprobs

                break
            
        discountedPayoffs = terminalPayoffs
        for player, infoset, valid_actions, action, actionprob in reversed(histories):
            ev = discountedPayoffs[player]
            self.cfr_regret_update(ev, action, actionprob, infoset, valid_actions, player)
            discountedPayoffs[player] *= actionprob

    def cfr_strategy_update(self, reachprobs, sampleprobs, infoset, player, valid_actions):
        equal_probs = [1.0 / len(valid_actions) if action in valid_actions else 0 for action in range(self.num_of_actions) ]

        # Update the strategies and regrets for each infoset
        # Get the current CFR
        prev_cfr = None
        if infoset in self.counterfactual_regret[player]:
            prev_cfr = self.counterfactual_regret[player][infoset]
        else:
            prev_cfr = [0 for _ in range(self.num_of_actions)]

        # Get the total positive CFR
        sumpos_cfr = float(sum([max(0,x) for x in prev_cfr]))
        if sumpos_cfr == 0:
            # Default strategy is equal probability
            probs = equal_probs
        else:
            # Use the strategy that's proportional to accumulated positive CFR
            probs = [max(0,x) / sumpos_cfr for x in prev_cfr]
        # Use the updated strategy as our current strategy
        self.sampling_strategies[player][infoset] = probs

        # Update the weighted policy probabilities (used to recover the average strategy)
        if infoset not in self.action_reachprobs[player]:
            self.action_reachprobs[player][infoset] = [0 for _ in range(self.num_of_actions)] 

        for i in range(self.num_of_actions):
            self.action_reachprobs[player][infoset][i] += reachprobs[player] * probs[i] / sampleprobs
        if sum(self.action_reachprobs[player][infoset]) == 0:
            # Default strategy is equal weight
            self.average_strategies[player][infoset] = equal_probs

        else:
            # Recover the weighted average strategy
            self.average_strategies[player][infoset] = [self.action_reachprobs[player][infoset][i] / sum(self.action_reachprobs[player][infoset]) for i in range(3)]
        # Return and use the current CFR strategy

        return self.sampling_strategies[player]

    def cfr_regret_update(self, ev, action, actionprob, infoset, valid_actions, player):
        if infoset not in self.counterfactual_regret[player]:
            self.counterfactual_regret[player][infoset] = [0 for _ in range(self.num_of_actions)] 

        for i in valid_actions:
            immediate_cfr = -ev * actionprob
            if action == i:
                immediate_cfr += ev
            self.counterfactual_regret[player][infoset][i] += immediate_cfr

    def fixed_strategy(self):
        sampled_strategies = [{} for _ in range(self.n_players)]
        for player, strategy in enumerate(self.sampling_strategies):
            for infoset, probs in strategy.items():
                action = self.sample_action(strategy, infoset)
                sampled_strategies[player][infoset] = action
        return sampled_strategies