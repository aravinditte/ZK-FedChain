import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical

class DataHandler:
    def __init__(self, data_path):
        self.data_path = data_path
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None

    def load_data(self):
        # This is a placeholder. In a real-world scenario, you'd load your actual dataset.
        # For this example, we'll generate some random data.
        x = np.random.rand(1000, 28, 28, 1)  # Simulating image data
        y = np.random.randint(0, 10, 1000)  # 10 classes

        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    def preprocess_data(self):
        # Normalize the data
        self.x_train = self.x_train.astype('float32') / 255
        self.x_test = self.x_test.astype('float32') / 255

        # Convert class vectors to binary class matrices
        self.y_train = to_categorical(self.y_train, 10)
        self.y_test = to_categorical(self.y_test, 10)

    def get_train_data(self):
        return self.x_train, self.y_train

    def get_test_data(self):
        return self.x_test, self.y_test
