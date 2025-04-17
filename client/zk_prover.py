import hashlib

class ZKProver:
    def generate_gradient_proof(self, gradients):
        data = str(gradients).encode()
        proof = hashlib.sha256(data).hexdigest()
        return f"0x{proof}", f"0x{proof[:8]}"
    
    def generate_training_proof(self, model_weights, accuracy):
        data = str(model_weights + [accuracy]).encode()
        proof = hashlib.sha256(data).hexdigest()
        return f"0x{proof}", f"0x{proof[:8]}"
