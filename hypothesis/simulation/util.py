import torch



def sample_joint(simulator, prior, n=1):
    r""""""
    inputs = prior.sample(torch.Size([n])).view(n, -1)
    outputs = simulator(inputs)

    return inputs, outputs



def joint_sampler(simulator, prior):
    yield sample_joint(simulator, prior)



def sample_marginal(simulator, prior, n=1):
    r""""""
    _, outputs = sample_joint(simulator, prior, n=n)

    return outputs



def marginal_sampler(simulator, prior):
    yield sample_marginal(simulator, prior)
