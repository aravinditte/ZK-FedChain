import unittest
import sys
import os

# Add parent directory to path to import client modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.data_handler import DataHandler
from client.model_trainer import ModelTrainer
from client.zk_prover import ZKProver

class TestLocalFunctionality(unittest.TestCase):
    def setUp(self):
        self.data_handler = DataHandler('dummy_path')
        self.model_trainer = ModelTrainer()
        self.zk_prover = ZKProver()

    def test_data_loading(self):
        self.data_handler.load_data()
        x_train, y_train = self.data_handler.get_train_data()
        self.assertIsNotNone(x_train)
        self.assertIsNotNone(y_train)

    def test_model_training(self):
        self.data_handler.load_data()
        self.data_handler.preprocess_data()
        x_train, y_train = self.data_handler.get_train_data()
        history = self.model_trainer.train(x_train, y_train, epochs=1)
        self.assertIn('accuracy', history.history)

    def test_gradient_computation(self):
        self.data_handler.load_data()
        self.data_handler.preprocess_data()
        x_train, y_train = self.data_handler.get_train_data()
        gradients = self.model_trainer.get_gradients(x_train[:1], y_train[:1])
        self.assertIsNotNone(gradients)

    def test_zk_proof_generation(self):
        self.data_handler.load_data()
        self.data_handler.preprocess_data()
        x_train, y_train = self.data_handler.get_train_data()
        gradients = self.model_trainer.get_gradients(x_train[:1], y_train[:1])
        proof, public_inputs = self.zk_prover.generate_gradient_proof(gradients)
        self.assertIsNotNone(proof)
        self.assertIsNotNone(public_inputs)

if __name__ == '__main__':
    unittest.main()
