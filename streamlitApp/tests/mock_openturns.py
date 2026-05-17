"""
Mock OpenTURNS module for testing when the real OpenTURNS is not available.
"""

import numpy as np


class Sample:
    """Mock OpenTURNS Sample class."""
    
    def __init__(self, data):
        if isinstance(data, np.ndarray):
            self.data = data
        else:
            self.data = np.array(data)
        self.size = self.data.shape[0]
        self.dimension = self.data.shape[1] if len(self.data.shape) > 1 else 1
        self.descriptions = ["Latitude", "Longitude", "Elevation", "Time", "Speed"]
    
    def getSize(self):
        return self.size
    
    def getDimension(self):
        return self.dimension
    
    def getDescription(self):
        return self.descriptions
    
    def setDescription(self, descriptions):
        self.descriptions = descriptions
    
    def __getitem__(self, index):
        if isinstance(index, int):
            return Point(self.data[index])
        else:
            return Sample(self.data[index])
    
    def __len__(self):
        return self.size


class Point:
    """Mock OpenTURNS Point class."""
    
    def __init__(self, data):
        if isinstance(data, np.ndarray):
            self.data = data.flatten()
        else:
            self.data = np.array(data).flatten()
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __len__(self):
        return len(self.data)


class Mesh:
    """Mock OpenTURNS Mesh class."""
    
    def __init__(self, sample):
        self.sample = sample
        self.vertices_number = sample.getSize()
    
    def getVerticesNumber(self):
        return self.vertices_number


class Field:
    """Mock OpenTURNS Field class."""
    
    def __init__(self, mesh, values):
        self.mesh = mesh
        self.values = values


class ProcessSample:
    """Mock OpenTURNS ProcessSample class."""
    
    def __init__(self, mesh, size, dimension):
        self.mesh = mesh
        self.size = size
        self.dimension = dimension
        self.fields = []
    
    def getSize(self):
        return self.size
    
    def getDimension(self):
        return self.dimension
    
    def getTimeGrid(self):
        return self.mesh
    
    def computeQuantilePerComponent(self, quantiles):
        # Return mock quantile data
        results = []
        for q in quantiles:
            # Create a sample with the same size as the mesh
            quantile_data = np.random.normal(5.0, 1.0, self.mesh.vertices_number)
            results.append(Sample(quantile_data.reshape(-1, 1)))
        return results
    
    def __setitem__(self, index, field):
        self.fields.append(field)


class Normal:
    """Mock OpenTURNS Normal distribution."""
    
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std
    
    def getSample(self, size):
        return Sample(np.random.normal(self.mean, self.std, size))


# Mock module functions
def AbsoluteExponential(params1, params2):
    """Mock AbsoluteExponential covariance model."""
    return "AbsoluteExponential"


def GaussianProcess(cov_model, mesh):
    """Mock GaussianProcess."""
    return "GaussianProcess"


# Create module-level variables
Sample.BuildFromPoint = lambda points: Sample(points)
