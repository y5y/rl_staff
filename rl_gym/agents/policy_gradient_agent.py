import sys
import timeit
import numpy as np
import tensorflow as tf

from rl_gym.models.tf_layers import HiddenLayer

# approximates pi(a | s)
class PolicyModel:
    def __init__(self, D, K, hidden_layer_sizes, lr=10e-2):
        # create the graph
        # K = number of actions
        self.layers = []
        M1 = D
        for M2 in hidden_layer_sizes:
            layer = HiddenLayer(M1, M2)
            self.layers.append(layer)
            M1 = M2

        # final layer
        # layer = HiddenLayer(M1, K, lambda x: x, use_bias=False)
        layer = HiddenLayer(M1, K, tf.nn.softmax, use_bias=False)
        self.layers.append(layer)

        # inputs and targets
        self.X = tf.placeholder(tf.float32, shape=(None, D), name='X')
        self.actions = tf.placeholder(tf.int32, shape=(None,), name='actions')
        self.advantages = tf.placeholder(tf.float32, shape=(None,), name='advantages')

        # calculate output and cost
        Z = self.X
        for layer in self.layers:
            Z = layer.forward(Z)
        p_a_given_s = Z
        # action_scores = Z
        # p_a_given_s = tf.nn.softmax(action_scores)
        # self.action_scores = action_scores
        self.predict_op = p_a_given_s

        # self.one_hot_actions = tf.one_hot(self.actions, K)

        selected_probs = tf.log(
          tf.reduce_sum(
            p_a_given_s * tf.one_hot(self.actions, K),
            reduction_indices=[1]
          )
        )

        # self.selected_probs = selected_probs
        cost = -tf.reduce_sum(self.advantages * selected_probs)
        optimizer = tf.train.AdagradOptimizer(learning_rate=lr)

        gvs = optimizer.compute_gradients(cost)
        capped_gvs = [(tf.clip_by_average_norm(grad, 1.0), var) for grad, var in gvs]
        self.train_op = optimizer.apply_gradients(capped_gvs)

        # gradients, variables = zip(*optimizer.compute_gradients(cost))
        # gradients, _ = tf.clip_by_global_norm(gradients, 100.0)
        # self.train_op = optimizer.apply_gradients(zip(gradients, variables))

    def set_session(self, session):
        self.session = session

    def partial_fit(self, X, actions, advantages):
        X = np.atleast_2d(X)
        actions = np.atleast_1d(actions)
        advantages = np.atleast_1d(advantages)
        self.session.run(
          self.train_op,
          feed_dict={
            self.X: X,
            self.actions: actions,
            self.advantages: advantages,
          }
        )

    def predict(self, X):
        X = np.atleast_2d(X)
        return self.session.run(self.predict_op, feed_dict={self.X: X})

    def sample_action(self, X):
        p = self.predict(X)[0]
        return np.random.choice(len(p), p=p)


# approximates V(s)
class ValueModel:
    def __init__(self, D, hidden_layer_sizes, lr=10e-5):
        # create the graph
        self.layers = []
        M1 = D
        for M2 in hidden_layer_sizes:
            layer = HiddenLayer(M1, M2)
            self.layers.append(layer)
            M1 = M2

        # final layer
        layer = HiddenLayer(M1, 1, lambda x: x)
        self.layers.append(layer)

        # inputs and targets
        self.X = tf.placeholder(tf.float32, shape=(None, D), name='X')
        self.Y = tf.placeholder(tf.float32, shape=(None,), name='Y')

        # calculate output and cost
        Z = self.X
        for layer in self.layers:
            Z = layer.forward(Z)
        Y_hat = tf.reshape(Z, [-1]) # the output
        self.predict_op = Y_hat

        cost = tf.reduce_sum(tf.square(self.Y - Y_hat))
        self.train_op = tf.train.GradientDescentOptimizer(learning_rate=lr).minimize(cost)

    def set_session(self, session):
        self.session = session

    def partial_fit(self, X, Y):
        X = np.atleast_2d(X)
        Y = np.atleast_1d(Y)
        self.session.run(self.train_op, feed_dict={self.X: X, self.Y: Y})

    def predict(self, X):
        X = np.atleast_2d(X)
        return self.session.run(self.predict_op, feed_dict={self.X: X})

class PolicyGradientAgent(object):
    def __init__(self, actor, critic, eps=1.0, eps_decay = 0.99, eps_min=0, gamma=0.9, verbose=False):
        self.actor_model = actor
        self.critic_model = critic
        self.eps = eps
        self.gamma = gamma
        self.eps_decay = eps_decay
        self.eps_min = eps_min
        self.random_actions = 0
        self.greedy_actions = 0
        self.epoch = 0
        self.verbose = verbose

        init = tf.global_variables_initializer()
        self.session = tf.InteractiveSession()
        self.session.run(init)
        actor.set_session(self.session)
        critic.set_session(self.session)

    '''
    Interface method
    '''
    def single_episode_train(self, env):
        steps = 0
        done = False
        s = env.reset()
        total_return = 0
        actions = []
        n_actions = env.action_space.n
        while not done:
            # predict action probabilities by critic model
            y_s = self.actor_model.predict(s).squeeze()
            if self.verbose:
                print("Step %d:" % steps)
                print("Observed state %s. Predicted critic values: %s" % (s, y_s))
            # choose action according to critic's probability predition
            a = np.random.choice(n_actions, p=y_s)
            actions.append(a)
            s2, r, done, _ = env.step(a)
            total_return += r

            if not done:
                y_s2 = self.critic_model.predict(s2)
                G = r + self.gamma * y_s2
            else:
                G = r
            advantage = G - self.critic_model.predict(s)

            if self.verbose:
                if not done:
                    print("Next state %s. Predicted value: %s" % (s2, y_s2))
                    print("G = %f + %f*%f = %f" % (r, self.gamma, y_s2, G))
                else:
                    print("G = %f" % r)

            # update the models
            self.actor_model.partial_fit(s, a, advantage)
            self.critic_model.partial_fit(s, G)

            steps += 1
            s = s2

        self.epoch += 1
        # if self.eps > self.eps_min:
        #     self.eps *= self.eps_decay
        if self.verbose:
            print("Actions sequence for this episode:")
            print(actions)

        return steps, total_return, r

    '''
    Interface method
    '''
    def optimal_action(self, s, action_space):
        y = self.actor_model.predict(s).squeeze()
        a_good = np.random.choice(action_space, p=y)
        # a_bad = np.argmax(y)
        return a_good