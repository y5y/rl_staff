import gym
import numpy as np
import pandas as pd
import os

from gym import wrappers
from datetime import datetime

from rl.models.linear_models import RbfRegressor
from rl.models.mlp_models import FeedForwardModel
from rl.agents.qlearning_agent import QLearningFunctionAproximationAgent

import matplotlib.pyplot as plt
import shutil

def create_model(env, model_name, verbose=False):
    obs = env.reset()
    obs_dim = len(obs)
    if model_name == 'rbf':
        # observation_examples = np.array([env.observation_space.sample() for x in range(10000)])
        # NOTE!! state samples are poor, b/c you get velocities --> infinity
        observation_examples = np.random.random((20000, 4)) * 2 - 1
        model = RbfRegressor(in_size=obs_dim, num_features=1000, output_size=env.action_space.n, gammmas=[1.0, 0.5, 0.1, 0.05], verbose=verbose)
        model.fit_features(observation_examples, env)
        gamma = 0.99
    elif model_name == 'ff':
        model = FeedForwardModel(in_size=obs_dim, out_sizes=[128, 64, 32, env.action_space.n],verbose=verbose)
        gamma = 0.9

    return model, gamma

def set_monitor(env):
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, os.pardir)
    filename = os.path.basename(__file__).split('.')[0]
    monitor_dir = filename + '_' + str(datetime.now()).replace(' ', '_').replace(':', '_')
    monitor_dir = os.path.join(base_dir, 'temp', monitor_dir)
    print("Writing results to %s" % monitor_dir)
    return wrappers.Monitor(env, monitor_dir, force=True)
    
np.random.seed(0)
if __name__ == '__main__':
    env = gym.make('CartPole-v0')
    env.seed(0)
    verbose = False
    models = ['rbf', 'ff']
    model, gamma = create_model(env, models[1], verbose=verbose)

    agent = QLearningFunctionAproximationAgent(model=model, eps_decay=0.98, gamma=gamma, verbose=verbose)

    monitor = False
    if monitor:
        env = set_monitor(env)

    num_iter = 500
    total_steps = 0
    returns = []
    for i in range(num_iter):
        print("Episode %d" % i)
        steps, tot_ret, last_reward = agent.single_episode_train(env)
        total_steps += steps
        returns.append(tot_ret)
        # if i > 0 and (i % 50 == 0):
        #     model.adjust()
        print('Episode finished in %d steps. Return %f.' % (steps, tot_ret))

    env.close()

    cum_returns = (pd.DataFrame(returns, columns=['r'])).r.rolling(window=100).mean()

    print("Last 100 episode average reward %f" % np.mean(returns[-100:]))

    fig, ax = plt.subplots()
    ax.plot(returns, label='Returns')
    ax.plot(cum_returns, label='Cumulative return')

    plt.show()
    print('Done')