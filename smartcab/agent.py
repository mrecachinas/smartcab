import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator
import itertools

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        self.run_type = 'intelligent'
        self.learning_rate = 0.4
        self.discount_factor = 0.25
        moves = ['left', 'right', 'forward']
        lights = ['green', 'red']
        self.pens = 0
        self.total_pens = 0
        self.tots = 0
        self.total_tots = 0
        self.actions_avail = 0
        left = (True, False)
        right = (True, False)
        self.Q_values = {((move, light, wait_left, wait_right), action): 10.0 \
                            for action in self.env.valid_actions 
                            for move, light, wait_left, wait_right in itertools.product(moves, lights, left, right)}
        print len(self.Q_values.keys())

    def reset(self, destination=None):
        self.total_pens += self.pens
        self.total_tots += self.tots
        print "num pens",self.pens, self.total_pens, self.total_tots, self.actions_avail
        self.pens = 0
        self.tots = 0
        self.planner.route_to(destination)

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        wait_for_left_turn = inputs["light"] == "green" and inputs["oncoming"] == "forward"
        wait_for_right_turn = inputs["light"] == "red" and inputs["left"] == "forward"
        self.state = (self.next_waypoint, inputs["light"], wait_for_left_turn, wait_for_right_turn)
        
        if self.run_type == 'random':
            action = random.choice(self.env.valid_actions)
        else:
            q, action = self.get_max_Q(self.state, self.env.valid_actions)

        # Execute action and get reward
        reward = self.env.act(self, action)
        if reward < 0:
            self.pens += 1
#            print reward
        self.tots += 1
        self.actions_avail += len(self.env.valid_actions)

        if self.run_type != 'random':
            self.update_q(self.planner.next_waypoint(), 
                     self.env.sense(self), 
                     action, 
                     q, 
                     reward,
                     self.env.valid_actions, 
                     self.discount_factor, 
                     self.learning_rate)

            #print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

    def update_q(self, next_waypoint, inputs, action, q, reward, valid_actions, discount_factor, learning_rate):
        wait_for_left_turn = inputs["light"] == "green" and inputs["oncoming"] == "forward"
        wait_for_right_turn = inputs["light"] == "red" and inputs["left"] == "forward"
        state_prime = (next_waypoint, inputs["light"], wait_for_left_turn, wait_for_right_turn)
        max_q, action_prime = self.get_max_Q(state_prime, valid_actions)
        q += learning_rate * (reward + discount_factor * max_q - q)
        self.Q_values[(self.state, action)] = q

    def get_max_Q(self, state, actions):
        return max((self.Q_values[(state, act)], act) for act in actions)

def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Now simulate it
    sim = Simulator(e, update_delay=0.01, display=False)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=100)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line


if __name__ == '__main__':
    run()
