import os
import json
import time
import sys

# Add parent directory to Python path to find client modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from web3 import Web3

# Now import using relative paths within the server directory
from server.aggregator import Aggregator
from server.ipfs_handler import IPFSHandler

# And import from client directory using the updated path
from client.blockchain_client import BlockchainClient

load_dotenv()

class Orchestrator:
    def __init__(self, blockchain_client, ipfs_handler, aggregator):
        self.blockchain_client = blockchain_client
        self.ipfs_handler = ipfs_handler
        self.aggregator = aggregator
        
        # Admin account for contract interactions
        self.admin_address = os.getenv('ADMIN_ADDRESS')
        self.admin_private_key = os.getenv('ADMIN_PRIVATE_KEY')

    def start_round(self):
        current_round = self.blockchain_client.get_current_round()
        current_model = self.blockchain_client.get_current_model()
        print(f"Starting round {current_round} with model {current_model}")
        # In a real system, you would notify clients here

    def collect_gradients(self, round_id):
        # Get participants who submitted gradients for this round
        participants = self.blockchain_client.contract.functions.getRoundParticipants(round_id).call()
        
        for participant in participants:
            # Get gradient IPFS hash from the contract
            gradient_hash = self.blockchain_client.contract.functions.rounds(round_id).call()[participant]
            
            # Download gradient from IPFS
            gradient_data = self.ipfs_handler.get_json(gradient_hash)
            
            # Add to aggregator
            self.aggregator.add_gradient(gradient_data)
            
        return len(participants)

    def aggregate_and_update(self, round_id):
        num_participants = self.collect_gradients(round_id)
        
        if num_participants < 3:
            print(f"Not enough participants ({num_participants}) for round {round_id}")
            return False
        
        # Aggregate gradients
        aggregated_gradients = self.aggregator.aggregate()
        
        # Get current model
        current_model_hash = self.blockchain_client.get_current_model()
        current_model_data = self.ipfs_handler.get_json(current_model_hash)
        
        # Apply aggregated gradients to model
        from client.model_trainer import ModelTrainer
        model = ModelTrainer()
        model.set_weights(current_model_data)
        model.apply_gradients(aggregated_gradients)
        
        # Save updated model to IPFS
        updated_weights = model.get_weights()
        model_hash = self.ipfs_handler.add_json(updated_weights)
        
        # Generate ZK proof for aggregation
        from client.zk_prover import ZKProver
        prover = ZKProver()
        accuracy = 85  # Placeholder accuracy
        proof, public_inputs = prover.generate_training_proof(updated_weights, accuracy)
        
        # Update blockchain with new model
        nonce = self.blockchain_client.w3.eth.get_transaction_count(self.admin_address)
        txn = self.blockchain_client.contract.functions.updateModel(
            round_id, 
            model_hash, 
            accuracy * 100,  # Scale by 100 for on-chain representation
            f"ipfs://{model_hash}", 
            bytes.fromhex(proof[2:]),  # Remove 0x prefix
            bytes.fromhex(public_inputs[2:])  # Remove 0x prefix
        ).build_transaction({
            'from': self.admin_address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.blockchain_client.w3.eth.gas_price
        })
        
        signed_txn = self.blockchain_client.w3.eth.account.sign_transaction(txn, self.admin_private_key)
        tx_hash = self.blockchain_client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.blockchain_client.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"Model updated for round {round_id}, transaction: {receipt.transactionHash.hex()}")
        return True

    def distribute_rewards(self, round_id):
        # Get participants
        participants = self.blockchain_client.contract.functions.getRoundParticipants(round_id).call()
        
        # Simple reward calculation - equal distribution
        reward_per_participant = 100 * 10**18  # 100 tokens
        rewards = [reward_per_participant] * len(participants)
        
        # Distribute rewards
        nonce = self.blockchain_client.w3.eth.get_transaction_count(self.admin_address)
        txn = self.blockchain_client.contract.functions.distributeRewards(
            round_id, participants, rewards
        ).build_transaction({
            'from': self.admin_address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': self.blockchain_client.w3.eth.gas_price
        })
        
        signed_txn = self.blockchain_client.w3.eth.account.sign_transaction(txn, self.admin_private_key)
        tx_hash = self.blockchain_client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.blockchain_client.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"Rewards distributed for round {round_id}, transaction: {receipt.transactionHash.hex()}")

    def run_federated_learning(self, num_rounds):
        for _ in range(num_rounds):
            self.start_round()
            round_id = self.blockchain_client.get_current_round()
            
            # Wait for round to complete
            round_info = self.blockchain_client.contract.functions.rounds(round_id).call()
            end_time = round_info[1]  # endTime
            
            current_time = int(time.time())
            if current_time < end_time:
                wait_time = end_time - current_time
                print(f"Waiting {wait_time} seconds for round {round_id} to complete...")
                time.sleep(wait_time)
            
            # Finalize round if not already finalized
            if not round_info[2]:  # finalized
                nonce = self.blockchain_client.w3.eth.get_transaction_count(self.admin_address)
                txn = self.blockchain_client.contract.functions.finalizeRound(round_id).build_transaction({
                    'from': self.admin_address,
                    'nonce': nonce,
                    'gas': 2000000,
                    'gasPrice': self.blockchain_client.w3.eth.gas_price
                })
                
                signed_txn = self.blockchain_client.w3.eth.account.sign_transaction(txn, self.admin_private_key)
                tx_hash = self.blockchain_client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                self.blockchain_client.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Aggregate and update model
            success = self.aggregate_and_update(round_id)
            
            if success:
                # Distribute rewards
                self.distribute_rewards(round_id)

if __name__ == "__main__":
    # Initialize components
    blockchain_client = BlockchainClient()
    ipfs_handler = IPFSHandler()
    aggregator = Aggregator()
    
    # Create orchestrator
    orchestrator = Orchestrator(blockchain_client, ipfs_handler, aggregator)
    
    # Run federated learning for 5 rounds
    print("Starting ZK-FedChain orchestrator...")
    orchestrator.run_federated_learning(5)