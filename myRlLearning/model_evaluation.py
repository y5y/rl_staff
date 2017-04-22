'''
Created on Apr 22, 2017

@author: Yury
'''

import numpy as np

from simple_value_table_agent import SimpleValueTableAgent
from policy_iteration_agent import PolicyIterationAgent
from grid_world import GridWorldSolver, EnvironmentFactory, REWARD_GOAL

if __name__ == '__main__':
    verbosity = 2  # 0 - no verbosity; 1 - show prints between episodes; 2 - show agent log
    env_factory = EnvironmentFactory(EnvironmentFactory.EnvironmentType.AllRandom)
    env = env_factory.create_environment()
    
    agent = PolicyIterationAgent(env.num_states, env.all_actions())
    agent.load_model('vtable.bin')
    solver = GridWorldSolver(env_factory, agent)
    
    res = solver.evaluate(range(env.num_states), verbosity)
    print("Reward: %f" % res)