"""
Trains a parameterized classifier to use with approximate likelihood-ratios.
"""

import argparse
import torch
import numpy as np
import os

from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import StepLR
from torch.distributions.multivariate_normal import MultivariateNormal
from torch.distributions.uniform import Uniform
from tqdm import tqdm

from hypothesis.benchmark import circle


def main(arguments):
    # Data-source preperation.
    dataset = SimulationDataset(2 * arguments.size, dimensionality=arguments.dimensionality,
                                lower=arguments.lower, upper=arguments.upper)
    # Training preperation.
    ones = torch.ones(arguments.batch_size, 1)
    zeros = torch.zeros(arguments.batch_size, 1)
    criterion = torch.nn.BCELoss()
    classifier = allocate_classifier(arguments)
    optimizer = torch.optim.Adam(classifier.parameters(), lr=arguments.lr)
    scheduler = StepLR(optimizer, step_size=50, gamma=0.1)
    iterations = int(arguments.size / arguments.batch_size)
    # Training procedure.
    for epoch in tqdm(range(arguments.epochs)):
        scheduler.step()
        loader = iter(DataLoader(dataset, num_workers=arguments.workers, batch_size = arguments.batch_size))
        for iteration in tqdm(range(iterations)):
            theta, x_theta = next(loader)
            _, x_theta_hat = next(loader)
            x = torch.cat([theta, x_theta], dim=1).detach()
            x_hat = torch.cat([theta, x_theta_hat], dim=1).detach()
            y = classifier(x)
            y_hat = classifier(x_hat)
            loss = criterion(y, zeros) + criterion(y_hat, ones)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        # Save the model at the current epoch.
        save_model(arguments, classifier, name="classifier_" + str(epoch))
    # Save the final model.
    save_model(arguments, classifier, name="classifier_final")


def save_model(arguments, model, name):
    # Check if an output directory has been specified.
    if arguments.out is not None:
        models_directory = arguments.out + '/'
    else:
        models_directory = "models/"

    if not os.path.exists(models_directory):
        os.makedirs(models_directory)

    iterations = [x for x in os.listdir(models_directory) if "iteration" in x]
    current_iteration = len(iterations)
    # If end of 1st epoch, create new dir
    if(name.split("_")[1] == "0"):
         current_iteration += 1

    models_directory += "iteration{}/".format(current_iteration)
    if not os.path.exists(models_directory):
        os.makedirs(models_directory)

    path = models_directory + name + ".th"
    torch.save(model, path)


def allocate_classifier(arguments):
    modules = []

    hidden = arguments.hidden
    # Add initial layer.
    modules.append(torch.nn.Linear(arguments.dimensionality + 32*32, hidden))
    modules.append(torch.nn.LeakyReLU())
    # Add hidden layers.
    for i in range(arguments.layers):
        modules.append(torch.nn.Linear(hidden, hidden))
        modules.append(torch.nn.LeakyReLU())
    # Add final layers.
    modules.append(torch.nn.Linear(arguments.hidden, 1))
    modules.append(torch.nn.Sigmoid())

    return torch.nn.Sequential(*modules)


def parse_arguments():
    parser = argparse.ArgumentParser("Likelihood-free Posterior Sampling. Demonstration 1 - Training.")
    parser.add_argument("--lr", type=float, default=0.00001, help="Learning-rate.")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch-size.")
    parser.add_argument("--lower", type=str, default="-0.9972356557846069, -0.06088715046644211, -0.03716924786567688", help="Lower-limit of the parameter space.")
    parser.add_argument("--upper", type=str, default="0.9964998960494995, 0.06596662104129791, 0.062344297766685486", help="Upper-limit of the parameter space.")
    parser.add_argument("--epochs", type=int, default=250, help="Number of data iterations.")
    parser.add_argument("--size", type=int, default=1000000, help="Number of samples in a single dataset.")
    parser.add_argument("--hidden", type=int, default=256, help="Number of hidden units.")
    parser.add_argument("--layers", type=int, default=3, help="Number of hidden layers.")
    parser.add_argument("--workers", type=int, default=0, help="Number of asynchronous data loaders.")
    parser.add_argument("--out", type=str, default=None, help="Directory to store the models.")
    parser.add_argument("--dimensionality", type=int, default=3, help="Dimensionality of the multivariate normal.")
    arguments, _ = parser.parse_known_args()

    return arguments


class SimulationDataset(Dataset):

    def __init__(self, size, dimensionality, lower, upper):
        super(SimulationDataset, self).__init__()
        self.size = size
        self.dimensionality = dimensionality

        lower_bounds = lower.split(",")
        lower_bounds = [float(x) for x in lower_bounds]

        upper_bounds = upper.split(",")
        upper_bounds = [float(x) for x in upper_bounds]

        self.uniform_radius = Uniform(lower_bounds[0], upper_bounds[0])
        self.uniform_x = Uniform(lower_bounds[1], upper_bounds[1])
        self.uniform_y = Uniform(lower_bounds[2], upper_bounds[2])

    def __getitem__(self, index):
        return self.sample()

    def __len__(self):
        return self.size

    def sample(self):
        radius = self.uniform_radius.sample()
        coord_x = self.uniform_x.sample()
        coord_y = self.uniform_y.sample()

        theta = torch.cat((radius, coord_x), dim=0)
        theta = torch.cat((theta, coord_y), dim=0)

        _, x_o = circle.allocate_observations(theta, 1)
        return theta, x_o.view(-1)


if __name__ == "__main__":
    arguments = parse_arguments()
    main(arguments)
