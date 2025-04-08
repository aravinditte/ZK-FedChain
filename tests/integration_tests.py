import unittest
import sys
import os
import time
from dotenv import load_dotenv
from web3 import Web3

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.data_handler import DataHandler
from client.model_trainer import ModelTrainer
from client.zk_prover import ZKProver
from client.blockchain_client import BlockchainClient
from server.aggregator import Aggregator
from server.ipfs_handler import IPFSHandler
from server.orchestrator import Orchestrator

load_dotenv()

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Initialize components
        self.data_handler = DataHandler('dummy_path')
        self.data_handler.load_data()
        self.data_handler.preprocess_data()
        
        self.model_trainer = ModelTrainer()
        self.zk_prover = ZKProver()
        
        # For testing, we'll use a local Ganache instance
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_NODE_URL', 'http://localhost:8545')))
        
        # Assuming contracts are deployed and we have their addresses
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        
        self.blockchain_client = BlockchainClient()
        
        self.ipfs_handler = IPFSHandler()
        self.aggregator = Aggregator()
        
        self.orchestrator = Orchestrator(
            self.blockchain_client,
            self.ipfs_handler,
            self.aggregator
        )
        
        # Test accounts
        self.accounts = self.w3.eth.accounts
        self.admin = self.accounts[0]
        self.participants = self.accounts[1:4]  # Use 3 participants for testing
        
        # Set admin private key for testing
        self.admin_private_key = os.getenv('ADMIN_PRIVATE_KEY')

    def test_full_training_round(self):
        # 1. Register participants
        for participant in self.participants:
            # For testing, we'll use a dummy private key
            # In a real scenario, each participant would have their own private key
            private_key = self.admin_private_key  # Using admin key for testing only
            
            # Approve token spending first
            token_address = self.blockchain_client.contract.functions.fedToken().call()
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=self._get_token_abi()
            )
            
            # Approve tokens
            nonce = self.w3.eth.get_transaction_count(participant)
            txn = token_contract.functions.approve(
                self.contract_address,
                100 * 10**18  # 100 tokens
            ).build_transaction({
                'from': participant,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Register participant
            self.blockchain_client.register_participant(participant, private_key)
        
        # 2. Start a training round
        current_round = self.blockchain_client.get_current_round()
        
        # 3. Each participant trains locally and submits gradients
        for participant in self.participants:
            # Get training data (in a real scenario, each would have different data)
            x_train, y_train = self.data_handler.get_train_data()
            
            # Train locally
            local_trainer = ModelTrainer()
            local_trainer.train(x_train, y_train, epochs=1)
            
            # Get gradients
            gradients = local_trainer.get_gradients(x_train[:1], y_train[:1])
            
            # Generate ZK proof
            proof, public_inputs = self.zk_prover.generate_gradient_proof(gradients)
            
            # Save gradients to IPFS
            gradients_list = [g.tolist() for g in gradients]
            gradient_hash = self.ipfs_handler.add_json(gradients_list)
            
            # Submit to blockchain
            private_key = self.admin_private_key  # Using admin key for testing only
            self.blockchain_client.submit_gradient(
                participant,
                private_key,
                current_round,
                gradient_hash,
                bytes.fromhex(proof[2:]),  # Remove 0x prefix
                bytes.fromhex(public_inputs[2:])  # Remove 0x prefix
            )
            
            # Add to aggregator for server-side processing
            self.aggregator.add_gradient(gradients)
        
        # 4. Wait for round to end
        round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
        end_time = round_info[1]  # endTime
        
        current_time = int(time.time())
        if current_time < end_time:
            wait_time = end_time - current_time
            time.sleep(wait_time + 1)  # Add 1 second buffer
        
        # 5. Finalize round
        nonce = self.w3.eth.get_transaction_count(self.admin)
        txn = self.blockchain_client.contract.functions.finalizeRound(current_round).build_transaction({
            'from': self.admin,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.admin_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 6. Aggregate and update model
        self.orchestrator.aggregate_and_update(current_round)
        
        # 7. Distribute rewards
        self.orchestrator.distribute_rewards(current_round)
        
        # 8. Verify the round was finalized
        round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
        self.assertTrue(round_info[2])  # finalized flag
        
        # 9. Verify rewards were distributed
        for participant in self.participants:
            reward = self.blockchain_client.contract.functions.getParticipantReward(current_round, participant).call()
            self.assertGreater(reward, 0)
    
    def _get_token_abi(self):
        # Simplified ERC20 ABI for testing
        return [
            {
                "constant": False,
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

if __name__ == '__main__':
    unittest.main()
