"""Markov Decision Processes (Chapter 17)

First we define an MDP, and the special case of a GridMDP, in which
states are laid out in a 2-dimensional grid.  We also represent a policy
as a dictionary of {state:action} pairs, and a Utility function as a
dictionary of {state:number} pairs.  We then define the value_iteration 
and policy_iteration algorithms."""

from utils import *
from random import *
import math
import sys

class MDP:
    """A Markov Decision Process, defined by an initial state, transition model,
    and reward function. We also keep track of a gamma value, for use by 
    algorithms. The transition model is represented somewhat differently from 
    the text.  Instead of T(s, a, s') being  probability number for each 
    state/action/state triplet, we instead have T(s, a) return a list of (p, s')
    pairs.  We also keep track of the possible states, terminal states, and 
    actions for each state. [page 615]"""

    def __init__(self, init, actlist, terminals, gamma=.9):
        update(self, init=init, actlist=actlist, terminals=terminals,
               gamma=gamma, states=set(), reward={})

    def R(self, state):
        "Return a numeric reward for this state."
        return self.reward[state]

    def T(state, action):
        """Transition model.  From a state and an action, return a list
        of (result-state, probability) pairs."""
        return NotImplemented

    def actions(self, state):
        """Set of actions that can be performed in this state.  By default, a 
        fixed list of actions, except for terminal states. Override this 
        method if you need to specialize by state."""
        if state in self.terminals:
            return [None]
        else:
            return self.actlist

class GridMDP(MDP):
    """A two-dimensional grid MDP, as in [Figure 17.1].  All you have to do is 
    specify the grid as a list of lists of rewards; use None for an obstacle
    (unreachable state).  Also, you should specify the terminal states.
    An action is an (x, y) unit vector; e.g. (1, 0) means move east."""
    def __init__(self, grid, terminals, init=(0, 0), gamma=.9):
        grid.reverse() ## because we want row 0 on bottom, not on top
        MDP.__init__(self, init, actlist=orientations,
                     terminals=terminals, gamma=gamma)
        update(self, grid=grid, rows=len(grid), cols=len(grid[0]))
        for x in range(self.cols):
            for y in range(self.rows):
                self.reward[x, y] = grid[y][x]
                if grid[y][x] is not None:
                    self.states.add((x, y))
        self.normalize_rewards()



    def print_rewards(self):
        sum = 0
        for x in range(self.cols):
            for y in range(self.rows):
                sum += abs(self.reward[x, y])

        for x in (range(self.cols)):
            for y in (range(self.rows)):
                print("%.2f" % round(self.reward[x, y]/sum,2)),
                # print("%.2f" % round(self.reward[x, y],2)),
            print(" ")


    # def modify_rewards_randomly(self, stdev = 0.5): #epsilon is the magnitude of random change
    #     sum = 0
    #     for x in range(self.cols):
    #         for y in range(self.rows):
    #             self.reward[x, y] *= 1 + gauss(0,stdev)
    #             sum += self.reward[x, y]
    #     k = 1 / sum
    #     for x in range(self.cols): #does normalization here
    #         for y in range(self.rows):
    #             self.reward[x, y] *= k


    def modify_rewards_randomly(self, step = 0.05): #epsilon is the magnitude of random change
        x_to_change = randint(0, self.cols-1)
        y_to_change = randint(0, self.rows-1)
        direction = randint(0,1) * 2 -1
        # print("Changing " + str(x_to_change) + " " + str(y_to_change) +" before "+ str(self.reward[x_to_change, y_to_change]))
        self.reward[x_to_change, y_to_change] += direction*step
        # print("Changing " + str(x_to_change) + " " + str(y_to_change) +" after "+ str(self.reward[x_to_change, y_to_change]))
        self.normalize_rewards()



    # normalizes the reward vector such that sum(R_i) = C and sum(|R_i|) = D
    def normalize_rewards(self, C = 1, D = 1):
        sum = 0
        abs_sum = 0
        for x in range(self.cols):
            for y in range(self.rows):
                if self.reward[x, y] != None:
                    sum += self.reward[x, y] #TODO handle None values here
                # abs_sum += abs(self.reward[x, y])

        # sum(R_i) = C normalization is done here
        k = C / (sum + 0.0000001) # a hack to prevent div by zero
        for x in range(self.cols): #does normalization here
            for y in range(self.rows):
                self.reward[x, y] *= k
        #         abs_sum += abs(self.reward[x, y])

        # sum(|R_i|) = D normalization is done here
        # abs_k = D / (abs_sum + 0.0000001)
        # for x in range(self.cols): #does normalization here
        #     for y in range(self.rows):
        #         self.reward[x, y] *= abs_k



    # def T(self, state, action):
    #     if action == None:
    #         return [(0.0, state)]
    #     else:
    #         return [(0.8, self.go(state, action)),
    #                 (0.1, self.go(state, turn_right(action))),
    #                 (0.1, self.go(state, turn_left(action)))]

    def T(self, state, action):
        if action == None:
            return [(0.0, state)]
        else:
            return [(1.0, self.go(state, action))]

    def go(self, state, direction):
        "Return the state that results from going in this direction."
        state1 = vector_add(state, direction)
        return if_(state1 in self.states, state1, state)

    def to_grid(self, mapping):
        """Convert a mapping from (x, y) to v into a [[..., v, ...]] grid."""
        return list(reversed([[mapping.get((x,y), None)
                               for x in range(self.cols)]
                              for y in range(self.rows)]))

    def to_arrows(self, policy):
        chars = {(1, 0):'>', (0, 1):'^', (-1, 0):'<', (0, -1):'v', None: '.'}
        return self.to_grid(dict([(s, chars[a]) for (s, a) in policy.items()]))

#______________________________________________________________________________


# Fig[17,1] = GridMDP([[-0.04, -0.04, -0.04, +1],
#                      [-0.04, None,  -0.04, -1],
#                      [-0.04, -0.04, -0.04, -0.04]],
#                     terminals=[(3, 2), (3, 1)])

# Test = GridMDP([[-0.04, -0.04, -0.04, +1],
#                 [-0.04, -0.04,  -0.04, -0.04],
#                 [-0.04, -0.04, -0.04, -0.04],
#                 [-0.04, -0.04, -0.04, -0.04]],
#                terminals=[(3, 3)])

#______________________________________________________________________________

def calculate_posterior(mdp, pi, U, expert_pi): #TODO add priors
    return calculate_conditional(mdp, pi, U, expert_pi) * calculate_cumulative_prior(mdp)

def calculate_cumulative_prior(mdp):
    product = 1
    for s in mdp.states:
        product *= calculate_prior(mdp.R(s))
    return product

def calculate_prior(R, Rmax = 1.0001):
    R = abs(R)
    # return 1/ (((R/Rmax)**0.5) * ((1 - R/Rmax)**0.5))
    return 1

def calculate_conditional(mdp, pi, U, expert_pi):
    return math.exp(min(calculate_qsum(mdp, pi, U, expert_pi), 709)) #exp(710) causes overflow

def calculate_qsum(mdp, pi, U, expert_pi):
    qsum = 0
    for s in mdp.states:
        qsum += calculate_q(s, expert_pi[s], mdp, U)
    return qsum

def calculate_q(s, a, mdp, U):
    R, T, gamma = mdp.R, mdp.T, mdp.gamma
    Q = R(s) + gamma * sum([p * U[s1] for (p, s1) in T(s, a)])
    return Q

#______________________________________________________________________________

def value_iteration(mdp, epsilon=0.001):
    "Solving an MDP by value iteration. [Fig. 17.4]"
    U1 = dict([(s, 0) for s in mdp.states])
    R, T, gamma = mdp.R, mdp.T, mdp.gamma
    while True:
        U = U1.copy()
        delta = 0
        for s in mdp.states:
            U1[s] = R(s) + gamma * max([sum([p * U[s1] for (p, s1) in T(s, a)])
                                        for a in mdp.actions(s)])
            delta = max(delta, abs(U1[s] - U[s]))
        if delta < epsilon * (1 - gamma) / gamma:
            return U

def best_policy(mdp, U):
    """Given an MDP and a utility function U, determine the best policy,
    as a mapping from state to action. (Equation 17.4)"""
    pi = {}
    for s in mdp.states:
        pi[s] = argmax(mdp.actions(s), lambda a:expected_utility(a, s, U, mdp))
    return pi

def expected_utility(a, s, U, mdp):
    "The expected utility of doing a in state s, according to the MDP and U."
    return sum([p * U[s1] for (p, s1) in mdp.T(s, a)])

#______________________________________________________________________________

def policy_iteration(mdp):
    "Solve an MDP by policy iteration [Fig. 17.7]"
    U = dict([(s, 0) for s in mdp.states])
    pi = dict([(s, choice(mdp.actions(s))) for s in mdp.states])
    while True:
        U = policy_evaluation(pi, U, mdp)
        unchanged = True
        for s in mdp.states:
            a = argmax(mdp.actions(s), lambda a: expected_utility(a,s,U,mdp))
            if a != pi[s]:
                pi[s] = a
                unchanged = False
        if unchanged:
            return pi

def policy_evaluation(pi, U, mdp, k=20):
    """Return an updated utility mapping U from each state in the MDP to its 
    utility, using an approximation (modified policy iteration)."""
    R, T, gamma = mdp.R, mdp.T, mdp.gamma
    for i in range(k):
        for s in mdp.states:
            U[s] = R(s) + gamma * sum([p * U[s] for (p, s1) in T(s, pi[s])])
    return U


