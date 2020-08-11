import math
import numpy as np
import torch

from scipy.stats import chi2



@torch.no_grad()
def highest_density_region(pdf, alpha, min_epsilon=10e-17):
    # Prepare posterior
    # Detect numpy type
    if type(pdf).__module__ != np.__name__:
        pdf = pdf.cpu().clone().numpy()
    else:
        pdf = np.array(pdf)
    total_pdf = pdf.sum()
    pdf /= total_pdf
    # Compute highest density level and the corresponding mask
    n = len(pdf)
    optimal_level = pdf.max().item()
    epsilon = 10e-02
    while epsilon >= min_epsilon:
        area = float(0)
        while area <= alpha:
            # Compute the integral
            m = (pdf >= optimal_level).astype(np.float32)
            area = np.sum(m * pdf)
            # Compute the error and apply gradient descent
            optimal_level -= epsilon
        optimal_level += 2 * epsilon
        epsilon /= 10

    return torch.from_numpy(m)


@torch.no_grad()
def highest_density_level(pdf, alpha, min_epsilon=10e-17, region=False):
    # Prepare posterior
    # Detect numpy type
    if type(pdf).__module__ != np.__name__:
        pdf = pdf.cpu().clone().numpy()
    else:
        pdf = np.array(pdf)
    total_pdf = pdf.sum()
    pdf /= total_pdf
    # Compute highest density level and the corresponding mask
    n = len(pdf)
    optimal_level = pdf.max().item()
    epsilon = 10e-02
    while epsilon >= min_epsilon:
        area = float(0)
        while area <= alpha:
            # Compute the integral
            m = (pdf >= optimal_level).astype(np.float32)
            area = np.sum(m * pdf)
            # Compute the error and apply gradient descent
            optimal_level -= epsilon
        optimal_level += 2 * epsilon
        epsilon /= 10
    optimal_level *= total_pdf
    if region:
        return optimal_level, torch.from_numpy(m)
    else:
        return optimal_level


@torch.no_grad()
def confidence_level(log_ratios, dof=None, level=0.95):
    if dof is None:
        dof = log_ratios.dim() - 1
    max_ratio = log_ratios[log_ratios.argmax()]
    test_statistic = -2 * (log_ratios - max_ratio)
    test_statistic -= test_statistic.min()
    level = chi2.isf(1 - level, df=dof)

    return test_statistic, level
