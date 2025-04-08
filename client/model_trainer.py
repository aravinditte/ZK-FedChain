import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

class ModelTrainer:
    def __init__(self):
        self.model = self.build_model()

    def build_model(self):
        model = Sequential([
            Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
            MaxPooling2D((2, 2)),
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Conv2D(64, (3, 3), activation='relu'),
            Flatten(),
            Dense(64, activation='relu'),
            Dense(10, activation='softmax')
        ])
        model.compile(optimizer='adam',
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])
        return model

    def train(self, x_train, y_train, epochs=5, batch_size=32):
        history = self.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.2)
        return history

    def evaluate(self, x_test, y_test):
        return self.model.evaluate(x_test, y_test)

    def get_gradients(self, x, y):
        with tf.GradientTape() as tape:
            predictions = self.model(x)
            loss = self.model.loss(y, predictions)
        return tape.gradient(loss, self.model.trainable_variables)

    def apply_gradients(self, gradients):
        self.model.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))

    def get_weights(self):
        return [w.numpy() for w in self.model.get_weights()]

    def set_weights(self, weights):
        self.model.set_weights(weights)
