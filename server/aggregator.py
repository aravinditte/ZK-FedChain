import numpy as np

class Aggregator:
    def __init__(self):
        self.gradients = []

    def add_gradient(self, gradient):
        self.gradients.append(gradient)

    def aggregate(self):
        # Simple FedAvg aggregation
        avg_gradients = [np.mean(grad, axis=0) for grad in zip(*self.gradients)]
        self.gradients = []  # Clear gradients after aggregation
        return avg_gradients

    def update_model(self, model, aggregated_gradients):
        model.apply_gradients(aggregated_gradients)
        return model
