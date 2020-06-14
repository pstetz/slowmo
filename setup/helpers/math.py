import numpy as np

def std_image(data, axis=3):
    """ Gets the std of the image over time """
    return np.std(data, axis=axis)

def mean_image(data, axis=3):
    """ Gets the mean of the image over time """
    return np.mean(data, axis=axis)

