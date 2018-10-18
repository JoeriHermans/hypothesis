"""
Transition proposals.
"""

import numpy as np
import torch

from torch.distributions.multivariate_normal import MultivariateNormal
from torch.distributions.normal import Normal
from torch.distributions.uniform import Uniform



class TransitionDistribution:

    def log_prob(self, thetas_current, thetas_next):
        raise NotImplementedError

    def sample(self, thetas, samples=1):
        raise NotImplementedError

    def is_symmetric(self):
        raise NotImplementedError


class SymmetricTransitionDistribution(TransitionDistribution):

    def is_symmetric(self):
        return True


class NormalTransitionDistribution(SymmetricTransitionDistribution):

    def __init__(self, sigma=1.):
        super(NormalTransitionDistribution, self).__init__()
        self._sigma = sigma

    def log_prob(self, thetas_current, thetas_next):
        normal = Normal(thetas_current, self._sigma)

        return normal.log_prob(thetas_next)

    def sample(self, thetas, samples=1):
        with torch.no_grad():
            size = torch.Size([samples])
            x_thetas = Normal(thetas.squeeze(), self._sigma).sample(size)

        return x_thetas.view(thetas.size(0), 1, samples)


class MultivariateNormalTransitionDistribution(SymmetricTransitionDistribution):

    def __init__(self, sigma):
        super(MultivariateNormalTransitionDistribution, self).__init__()
        self._dimensionality = sigma.size(0)
        self._sigma = sigma

    def log_prob(self, thetas_current, thetas_next):
        normal = MultivariateNormal(thetas_current, self._sigma)

        return normal.log_prob(thetas_next)

    def sample(self, thetas, samples=1):
        x = []

        with torch.no_grad():
            thetas = thetas.view(-1, self._dimensionality)
            size = torch.Size([samples])
            for theta in thetas:
                x_thetas = MultivariateNormal(theta.view(-1), self._sigma).sample(size).view(-1, self._dimensionality, samples)
                x.append(x_thetas)
            x = torch.cat(x, dim=0)

        return x


class UniformTransitionDistribution(SymmetricTransitionDistribution):

    def __init__(self, min_bound, max_bound):
        super(UniformTransitionDistribution, self).__init__()
        self._min_bound = torch.tensor(min_bound).float().view(-1, 1)
        self._max_bound = torch.tensor(max_bound).float().view(-1, 1)
        self._dimensionality = self._min_bound.size(0)
        self._distribution = Uniform(self._min_bound, self._max_bound)

    def log_prob(self, thetas_current, thetas_next):
        return self._distribution.log_prob(thetas_next)

    def sample(self, thetas, samples=1):
        x = []

        with torch.no_grad():
            thetas = thetas.view(-1, self._dimensionality)
            size = torch.Size([samples])
            for theta in thetas:
                x_thetas = self._distribution.sample(size).view(-1, self._dimensionality, samples)
                x.append(x_thetas)
            x = torch.cat(x, dim=0)

        return x
