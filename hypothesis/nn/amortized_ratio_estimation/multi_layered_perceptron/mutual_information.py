import hypothesis
import torch

from hypothesis.nn import MultiLayeredPerceptron
from hypothesis.nn.amortized_ratio_estimation import BaseMutualInformationRatioEstimator
from hypothesis.nn.neuromodulation import BaseNeuromodulatedModule
from hypothesis.nn.neuromodulation import allocate_neuromodulated_activation
from hypothesis.nn.neuromodulation import list_neuromodulated_modules
from hypothesis.nn.util import compute_dimensionality



class MutualInformationRatioEstimatorMLP(BaseMutualInformationRatioEstimator):

    def __init__(self,
        shape_inputs,
        shape_outputs,
        activation=hypothesis.default.activation,
        dropout=hypothesis.default.dropout,
        layers=hypothesis.default.trunk):
        super(MutualInformationRatioEstimatorMLP, self).__init__()
        dimensionality = compute_dimensionality(shape_inputs) + compute_dimensionality(shape_outputs)
        self.mlp = MultiLayeredPerceptron(
            shape_xs=(dimensionality,),
            shape_ys=(1,),
            activation=activation,
            dropout=dropout,
            layers=layers,
            transform_output=None)

    def log_ratio(self, x, y):
        features = torch.cat([x, y], dim=1)

        return self.mlp(features)



class MutualInformationRatioEstimatorNeuromodulatedMLP(BaseMutualInformationRatioEstimator):

    def __init__(self,
        shape_x,
        controller_allocator,
        activation=hypothesis.default.activation,
        dropout=hypothesis.default.dropout,
        layers=hypothesis.default.trunk):
        super(MutualInformationRatioEstimatorNeuromodulatedMLP, self).__init__()
        # Allocate the neuromodulated activation.
        neuromodulated_activation = allocate_neuromodulated_activation(
            activation=activation,
            allocator=controller_allocator)
        # Check if the specified activation is an i
        self.mlp = MultiLayeredPerceptron(
            shape_xs=shape_x,
            shape_ys=(1,),
            activation=neuromodulated_activation,
            dropout=dropout,
            layers=layers,
            transform_output=None)
        # List the neuromodulated modules.
        self.neuromodulated_modules = list_neuromodulated_modules(self)

    def log_ratio(self, x, y):
        for module in self.neuromodulated_modules:
            module.update(context=y)

        return self.mlp(x)
