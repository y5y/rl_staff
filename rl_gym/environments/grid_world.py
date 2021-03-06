'''
Created on Mar 13, 2017

@author: Yury
'''

from __future__ import print_function
import sys
import numpy as np
import timeit

REWARD_GOAL = 10
REWARD_PIT = -10
REWARD_STEP = -1
REWARD_HANG = -5

class EnvironmentFactory:
    class EnvironmentType:
        Deterministic = 0
        RandomPlayer = 1
        RandomPlayerAndGoal = 2
        RandomPlayerGoalAndPit = 3
        AllRandom = 4
        
    def __init__(self, env_type):
        self.env_type = env_type
        
    def create_environment(self, state=None):
        if self.env_type == EnvironmentFactory.EnvironmentType.Deterministic:
            cls = DeterministicEnvironment
        elif self.env_type == EnvironmentFactory.EnvironmentType.RandomPlayer:
            cls = RandomPlayerEnvironment
        elif self.env_type == EnvironmentFactory.EnvironmentType.RandomPlayerAndGoal:
            cls = RandomGoalAndPlayerEnvironment
        elif self.env_type == EnvironmentFactory.EnvironmentType.RandomPlayerGoalAndPit:
            cls = RandomGoalPlayerAndPitEnvironment
        elif self.env_type == EnvironmentFactory.EnvironmentType.AllRandom:
            cls = FullyRandomEnvironment
        else:
            cls = None
        
        if state == None:
            env = cls()
        else:
            env = cls.from_state(state)
        return env

class Action:
    num_actions = 4
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    @staticmethod
    def to_string(a, first_latter=False):
        if a == Action.UP:
            return 'U' if first_latter else 'UP'
        elif a == Action.DOWN:
            return 'D' if first_latter else 'DOWN'
        elif a == Action.LEFT:
            return 'L' if first_latter else 'LEFT'
        elif a == Action.RIGHT:
            return 'R' if first_latter else 'RIGHT'
        else:
            return 'n/a'
        
class EnvironmentBase(object):
    class ActionSpace:
        def __init__(self, n):
            self.n = n
            
        def sample(self):
            return np.random.choice(self.n)
        
    size = 4
    grid_size = size * size
    grid_size_square = grid_size ** 2
    grid_size_cube = grid_size ** 3
    __all_actions = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]
    action_space = ActionSpace(len(__all_actions))
    
    def __init__(self, player, goal, pit, wall, state):
        # Assume that all parameters are valid
        self.player = player
        self.player_cartesian = EnvironmentBase.abs_to_cartesian(player)
        self.goal = goal
        self.goal_cartesian = EnvironmentBase.abs_to_cartesian(goal)
        self.pit = pit
        self.pit_cartesian = EnvironmentBase.abs_to_cartesian(pit)
        self.wall = wall
        self.wall_cartesian = EnvironmentBase.abs_to_cartesian(wall)
        self.state = state
        self.steps = 0
    
    def __str__(self):
        return "state %d, player %d, goal %d, pit %d, wall %d" % (self.state, self.player, self.goal, self.pit, self.wall)
    
    def all_actions(self):
        return self.__all_actions
    
    @classmethod
    def action_to_str(cls, action):
        return Action.to_string(action)
    
    @classmethod
    def abs_to_cartesian(cls, abs_position):
        return (int(abs_position / cls.size), int(abs_position % cls.size))
    
    @classmethod
    def cartesian_to_abs(cls, cartesian_pos):
        return int(cartesian_pos[0] * cls.size + cartesian_pos[1])
    
    def reward(self):
        player_pos = self.player_abs_from_state(self.state)
        if player_pos == self.pit:
            return REWARD_PIT
        elif player_pos == self.goal:
            return REWARD_GOAL
        else:
            return REWARD_STEP
        
    def is_done(self):
        player_pos = self.player_abs_from_state(self.state)
        return player_pos == self.pit or player_pos == self.goal
    
    def render(self):
        self.show()
    
    # Simulate reset to match openai gym api
    def reset(self):
        return self.state
    
    def step(self, action):
        self.steps += 1
        # up (row - 1)
        if action == Action.UP:
            new_loc = (self.player_cartesian[0] - 1, self.player_cartesian[1])
        # down (row + 1)
        elif action == Action.DOWN:
            new_loc = (self.player_cartesian[0] + 1, self.player_cartesian[1])
        # left (column - 1)
        elif action == Action.LEFT:
            new_loc = (self.player_cartesian[0], self.player_cartesian[1] - 1)
        # right (column + 1)
        elif action == Action.RIGHT:
            new_loc = (self.player_cartesian[0], self.player_cartesian[1] + 1)

        if (new_loc != self.wall_cartesian):
            if ((np.array(new_loc) <= (3, 3)).all() and (np.array(new_loc) >= (0, 0)).all()):
                self.player_cartesian = new_loc
                self.player = EnvironmentBase.cartesian_to_abs(new_loc)
                self.state = self.player_abs_to_state(self.player)

        if self.steps < self.grid_size:
            return self.state, self.reward(), self.is_done(), None
        else:
            return self.state, REWARD_HANG, True, None
    
    '''
    This is cheat function for basic agent RL algorithms which require kind of God mode
    '''
    def simulate_step(self, action):
        cur_state = self.state
        cur_player = self.player
        cur_player_cart = self.player_cartesian
        
        res = self.step(action)
        
        # Undo step
        self.state = cur_state
        self.player = cur_player
        self.player_cartesian = cur_player_cart
                                     
        return res
    
    @classmethod
    def from_state(cls, state):
        player = cls.player_abs_from_state(state)
        goal = cls.goal_abs_from_state(state)
        pit = cls.pit_abs_from_state(state)
        wall = cls.wall_abs_from_state(state)
        
        # Check validity
        if player in [goal, pit, wall] or goal in [pit, wall] or pit in [wall]:
            return None
        
        return cls(player, goal, pit, wall, state)
    
    def show(self):
        print("** Grid world **")
        for i in range(self.size):
            print("----------------")
            for j in range(self.size):
                abs_pos = self.cartesian_to_abs((i, j))
                if abs_pos == self.wall:
                    symbol = '#'
                elif abs_pos == self.goal:
                    symbol = '+'
                elif abs_pos == self.pit:
                    symbol = '-'
                elif abs_pos == self.player:  
                    symbol = 'P'
                else:
                    symbol = ' '
                print((" %s |" % symbol), end='')
            print()
        print()
    
    def show_policy(self, policy):
        for i in range(self.size):
            print("----------------")
            for j in range(self.size):
                abs_pos = self.cartesian_to_abs((i, j))
                if abs_pos == self.wall:
                    symbol = '#'
                elif abs_pos == self.goal:
                    symbol = '+'
                elif abs_pos == self.pit:
                    symbol = '-'
                else:  
                    state = self.player_abs_to_state(abs_pos)
                    if state in policy:
                        action = policy[state]
                        symbol = Action.to_string(action, first_latter=True)
                    else:
                        symbol = '?'        
                        
                print((" %s |" % symbol), end='')
            print("")
        print("")
    
    def show_values(self, V):        
        for i in range(self.size):
            print("--------------------------------")
            for j in range(self.size):
                abs_pos = self.cartesian_to_abs((i, j))
                if abs_pos == self.wall:
                    symbol = '  #  '
                elif abs_pos == self.goal:
                    symbol = '  +  '
                elif abs_pos == self.pit:
                    symbol = '  -  '
                else:  
                    state = self.player_abs_to_state(abs_pos)
                    if state in V:
                        symbol = "%.2f" % (V[state])
                    else:
                        symbol = '?'
                print((" %s |" % symbol), end='')
            print("")
        print("")

class DeterministicEnvironment(EnvironmentBase):
    def __init__(self, player=None, goal=None, pit=None, wall=None, state=None):
        self.num_states = self.grid_size
        self.steps = 0
        
        if state != None:
            super(DeterministicEnvironment, self).__init__(player, goal, pit, wall, state)
        else:
            self.player = 0
            self.player_cartesian = EnvironmentBase.abs_to_cartesian(self.player)
            self.wall = 10
            self.wall_cartesian = (2, 2)
            self.goal = 15
            self.goal_cartesian = (3, 3)
            self.pit = 5
            self.pit_cartesian = (1, 1)
            
            self.state = self.player_abs_to_state(self.player)
    
    def player_abs_to_state(self, player_abs):
        # In this environment everything initialized deterministically. Player can change position so it's location represent the state of the world.
        return player_abs
    
    @classmethod
    def player_abs_from_state(cls, state):
        # State represent's player position
        return state
    
    @classmethod
    def goal_abs_from_state(cls, state):
        # In this environment goal is fixed
        return 15
    
    @classmethod
    def pit_abs_from_state(cls, state):
        # In this environment pit is fixed
        return 5
    
    @classmethod
    def wall_abs_from_state(cls, state):
        # In this environment wall is fixed
        return 10

class RandomPlayerEnvironment(DeterministicEnvironment):
    def __init__(self, player=None, goal=None, pit=None, wall=None, state=None):
        self.num_states = self.grid_size
        self.steps = 0
        
        if state != None:
            super(RandomPlayerEnvironment, self).__init__(player, goal, pit, wall, state)
        else:
            self.wall = 10
            self.wall_cartesian = (2, 2)
            self.goal = 15
            self.goal_cartesian = (3, 3)
            self.pit = 5
            self.pit_cartesian = (1, 1)
            
            # Initialize player random location
            self.player = np.random.choice(self.grid_size)
            while self.player in [self.wall, self.pit, self.goal]:
                self.player = np.random.choice(self.grid_size)
            self.player_cartesian = EnvironmentBase.abs_to_cartesian(self.player)
            self.state = self.player_abs_to_state(self.player)

class RandomGoalAndPlayerEnvironment(EnvironmentBase):
    def __init__(self, player=None, goal=None, pit=None, wall=None, state=None):
        self.steps = 0
        if state != None:
            super(RandomGoalAndPlayerEnvironment, self).__init__(player, goal, pit, wall, state)
        else:
            self.num_states = self.grid_size ** 2
            self.wall = 10
            self.wall_cartesian = (2, 2)
            self.pit = 5
            self.pit_cartesian = (1, 1)
    
            # Initialize goal random location
            self.goal = np.random.choice(self.grid_size)
            while self.goal in [self.wall, self.pit]:
                self.goal = np.random.choice(self.grid_size)
            self.goal_cartesian = (int(self.goal / self.size), int(self.goal % self.size))
            
            # Initialize player random location
            self.player = np.random.choice(self.grid_size)
            while self.player in [self.wall, self.pit, self.goal]:
                self.player = np.random.choice(self.grid_size)
            self.player_cartesian = EnvironmentBase.abs_to_cartesian(self.player)
            self.state = self.player_abs_to_state(self.player)
    
    def player_abs_to_state(self, player_abs):
        # We represent state as linear combination of (player and goal) were coordinates are (y,x) accordingly
        # So state = y*a + x where y is player coordinate and x - goal 
        return int(player_abs * self.grid_size + self.goal)
    
    @classmethod
    def player_abs_from_state(cls, state):
        # We need to find y coordinate from state = y*a + x so it just state/a
        return int(state / cls.grid_size)
    
    @classmethod
    def goal_abs_from_state(cls, state):
        # We need to find x coordinate from state = y*a + x so it just state mod a
        return int(state % cls.grid_size)
    
    @classmethod
    def pit_abs_from_state(cls, state):
        # In this environment pit is fixed
        return 5
    
    @classmethod
    def wall_abs_from_state(cls, state):
        # In this environment wall is fixed
        return 10

class RandomGoalPlayerAndPitEnvironment(EnvironmentBase):    
    def __init__(self, player=None, goal=None, pit=None, wall=None, state=None):
        self.steps = 0
        if state != None:
            super(RandomGoalPlayerAndPitEnvironment, self).__init__(player, goal, pit, wall, state)
        else:
            self.num_states = self.grid_size ** 3
            self.wall = 10
            self.wall_cartesian = (2, 2)
            
            # Initialize goal random location
            self.pit = np.random.choice(self.grid_size)
            while self.pit in [self.wall]:
                self.pit = np.random.choice(self.grid_size)
            self.pit_cartesian = (int(self.pit / self.size), int(self.pit % self.size))
    
            # Initialize goal random location
            self.goal = np.random.choice(self.grid_size)
            while self.goal in [self.wall, self.pit]:
                self.goal = np.random.choice(self.grid_size)
            self.goal_cartesian = (int(self.goal / self.size), int(self.goal % self.size))
    
            # Initialize player random location
            self.player = np.random.choice(self.grid_size)
            while self.player in [self.wall, self.pit, self.goal]:
                self.player = np.random.choice(self.grid_size)
            self.player_cartesian = EnvironmentBase.abs_to_cartesian(self.player)
            self.state = self.player_abs_to_state(self.player)
    
    def player_abs_to_state(self, player_abs):
        # We represent state as linear combination of (player, goal and pit) were coordinates are (z,y,x) accordingly
        # So state = z*a^2 + y*a + x where z is player coordinate, y - goal and x - pit 
        return int(player_abs * self.grid_size_square + self.goal * self.grid_size + self.pit)

    @classmethod
    def player_abs_from_state(cls, state):
        # We need to find z coordinate from state = z*a^2 + y*a + x
        return int(state / cls.grid_size_square)
        
    @classmethod
    def goal_abs_from_state(cls, state):
        # We need to find y coordinate from state = z*a^2 + y*a + x
        return int((state % cls.grid_size_square) / cls.grid_size)
    
    @classmethod
    def pit_abs_from_state(cls, state):
        # We need to find x coordinate from state = z*a^2 + y*a + x
        return int(float(state % cls.grid_size_square) % cls.grid_size)
    
    @classmethod
    def wall_abs_from_state(cls, state):
        # In this environment wall is fixed
        return 10


class FullyRandomEnvironment(EnvironmentBase):
    def __init__(self, player=None, goal=None, pit=None, wall=None, state=None):
        self.steps = 0
        if state != None:
            super(FullyRandomEnvironment, self).__init__(player, goal, pit, wall, state)
        else:
            self.num_states = self.grid_size ** 4
            # Initialize wall random location
            self.wall = np.random.choice(self.grid_size)
            self.wall_cartesian = (int(self.wall / self.size), int(self.wall % self.size))
            
            # Initialize goal random location
            self.pit = np.random.choice(self.grid_size)
            while self.pit in [self.wall]:
                self.pit = np.random.choice(self.grid_size)
            self.pit_cartesian = (int(self.pit / self.size), int(self.pit % self.size))
    
            # Initialize goal random location
            self.goal = np.random.choice(self.grid_size)
            while self.goal in [self.wall, self.pit]:
                self.goal = np.random.choice(self.grid_size)
            self.goal_cartesian = (int(self.goal / self.size), int(self.goal % self.size))
    
            # Initialize player random location
            self.player = np.random.choice(self.grid_size)
            while self.player in [self.wall, self.pit, self.goal]:
                self.player = np.random.choice(self.grid_size)
            self.player_cartesian = EnvironmentBase.abs_to_cartesian(self.player)
            self.state = self.player_abs_to_state(self.player)
    
    def player_abs_to_state(self, player_abs):
        # We represent state as linear combination of (player, goal, pit and wall) were coordinates are (z,y,x,w) accordingly
        # So state = z*a^3 + y*a^2 + x*a + w where z is player coordinate, y - goal and x - pit and w - wall 
        return int(player_abs * self.grid_size_cube + self.goal * self.grid_size_square + self.pit * self.grid_size + self.wall)

    @classmethod
    def player_abs_from_state(cls, state):
        # We need to find z coordinate from state = z*a^3 + y*a^2 + x*a + w
        return int(state / cls.grid_size_cube)
        
    @classmethod
    def goal_abs_from_state(cls, state):
        # We need to find y coordinate from state = z*a^3 + y*a^2 + x*a + w
        return int((state % cls.grid_size_cube) / cls.grid_size_square)
    
    @classmethod
    def pit_abs_from_state(cls, state):
        # We need to find x coordinate from state = z*a^3 + y*a^2 + x*a + w
        return int(((state % cls.grid_size_cube) % cls.grid_size_square) / cls.grid_size)
    
    @classmethod
    def wall_abs_from_state(cls, state):
        # We need to find w coordinate from state = z*a^3 + y*a^2 + x*a + w
        return int(((state % cls.grid_size_cube) % cls.grid_size_square) % cls.grid_size) 


class GridWorldSolver:
    def __init__(self, env_factory, agent):
        self.env_factory = env_factory
        self.agent = agent
    
    def train(self, states, verbosity=0):
        if verbosity >= 1:
            print("Train agent for %d iterations." % len(states))
            start_time = timeit.default_timer()
        
        steps = self.agent.single_iteration_train(self.env_factory, states, verbosity)

        if verbosity >= 1:
            elapsed = timeit.default_timer() - start_time
            print("Training time %.3f[ms]" % (elapsed * 1000))
        if verbosity == 0:
            print(" steps: %d" % steps)
        return steps
    
    def solve_world(self, env, star_state, max_steps=10000):
        actions = []
        steps = 0
        done = False
        total_reward = 0
        s = star_state
        while not done:
            next_move = self.agent.optimal_action(s, env.action_space.n)
            # make the move
            s, r, done, _ = env.step(next_move)
            total_reward += r
            actions.append(Action.to_string(next_move))
            steps += 1
            if steps > max_steps:
                break
            
        return actions, total_reward, r
    
    def evaluate(self, states, env_wrapper = None, verbosity=0):
        if verbosity >= 2:
            print("Evaluating agent for %d iterations." % len(states))
            start_time = timeit.default_timer()
        rewards = np.array([np.NAN] * (len(states)))
        num_iterations = len(states)
        for i in range(num_iterations):
            if i % 1000 == 0 and verbosity <= 1:
                sys.stdout.write('.')
                sys.stdout.flush()
            env = self.env_factory.create_environment(states[i])#TODO: fix this in case of Deterministic world and monte carlo agent
            if env == None:
                continue
            
            if verbosity >= 3:
                print()
                env.show()
            
            if env_wrapper != None:
                env_wrapper._env = env
                path, total_reward, last_action_reward = self.solve_world(env_wrapper, env_wrapper.state(), max_steps=env.grid_size)
            else:
                path, total_reward, last_action_reward = self.solve_world(env, env.state, max_steps=env.grid_size)
            
            if verbosity >= 3 or (verbosity >= 2 and last_action_reward != REWARD_GOAL):
                if last_action_reward != REWARD_GOAL:
                    print("Failed environment:")
                else:
                    print("Passed environment:")
                env = self.env_factory.create_environment(states[i])
                if env_wrapper != None:
                    env_wrapper._env = env
                    env = env_wrapper
                env.render()
                self.agent.display_functions(env)
                print("Agent path")
                print(path)
                print("Total Return: %.1f" % total_reward)
            rewards[i] = last_action_reward
        print()
        if verbosity >= 1:
            print("Valid states checked %d from total %d" % (num_iterations - len(rewards[np.isnan(rewards)]), num_iterations))
            success = rewards[rewards == REWARD_GOAL].size
            fail = rewards[rewards == REWARD_PIT].size
            hang = rewards[~np.isnan(rewards) & (rewards != REWARD_GOAL) & (rewards != REWARD_PIT)].size
            print("%d ended at goal, %d at pit, %d hanged." % (success, fail, hang))
        if verbosity >= 2:
            elapsed = timeit.default_timer() - start_time
            print("Evaluation time %.3f[ms]" % (elapsed * 1000))
        return np.nanmean(rewards)
