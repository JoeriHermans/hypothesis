import argparse
import hypothesis
import matplotlib.pyplot as plt
import numpy as np
import torch

from hypothesis.auto.training import LikelihoodToEvidenceRatioEstimatorTrainer as Trainer
from hypothesis.benchmark.normal import Prior
from hypothesis.benchmark.normal import Simulator
from hypothesis.nn.amortized_ratio_estimation import LikelihoodToEvidenceRatioEstimatorMLP as RatioEstimator
from hypothesis.visualization.util import make_square
from torch.utils.data import TensorDataset



def main(arguments):
    # Allocate the ratio estimator
    estimator = RatioEstimator(
        activation=torch.nn.SELU,
        layers=[128, 128, 128],
        shape_inputs=(1,),
        shape_outputs=(1,))
    estimator = estimator.to(hypothesis.accelerator)
    # Allocate the optimizer
    optimizer = torch.optim.Adam(estimator.parameters())
    # Allocate the trainer, or optimization procedure.
    trainer = Trainer(
        estimator=estimator,
        dataset_train=allocate_dataset_train(),
        dataset_test=allocate_dataset_test(),
        epochs=arguments.epochs,
        checkpoint=arguments.checkpoint,
        batch_size=arguments.batch_size,
        optimizer=optimizer)
    # Execute the optimization process.
    summary = trainer.fit()
    print(summary)
    # Plot the testing and training loss.
    figure, axes = plt.subplots(nrows=1, ncols=2, sharey=True)
    # Training
    ax = axes[0]
    loss = summary.train_losses(log=True)
    ax.plot(loss, lw=2, color="black")
    ax.set_xlabel("Gradient updates")
    ax.set_ylabel("Logarithmic loss")
    ax.set_title("Training loss")
    ax.minorticks_on()
    # Testing
    ax = axes[1]
    epochs = np.arange(summary.num_epochs()) + 1
    loss = summary.test_losses(log=True)
    plt.plot(epochs, loss, lw=2, color="black")
    ax.set_xlabel("Epochs")
    ax.set_title("Testing loss")
    # Square axes
    make_square(axes[0])
    make_square(axes[1])
    figure.tight_layout()
    plt.show()


def batch_feeder(batch, criterion, accelerator):
    inputs, outputs = batch
    inputs = inputs.to(accelerator, non_blocking=True)
    outputs = outputs.to(accelerator, non_blocking=True)

    return criterion(inputs=inputs, outputs=outputs)


def allocate_dataset_train():
    return allocate_dataset(100000)


def allocate_dataset_test():
    return allocate_dataset(1000)


@torch.no_grad()
def allocate_dataset(n):
    prior = Prior()
    simulator = Simulator()
    size = torch.Size([n])
    inputs = prior.sample(size).view(-1, 1)
    outputs = simulator(inputs).view(-1, 1)

    return TensorDataset(inputs, outputs)


def parse_arguments():
    parser = argparse.ArgumentParser("Amortized Likelihood-to-evidence Ratio Estimation: minimal example")
    parser.add_argument("--batch-size", type=int, default=hypothesis.default.batch_size, help="Batch-size of the stochastic optimization.")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to store the checkpoints. If specified, checkpointing will be enabled.")
    parser.add_argument("--epochs", type=int, default=10, help="Number of data epochs.")
    arguments, _ = parser.parse_known_args()

    return arguments


if __name__ == "__main__":
    arguments = parse_arguments()
    main(arguments)
