import os
import json
import time
import sys

# Add parent directory to Python path to find client modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from web3 import Web3

from server.aggregator import Aggregator
from server.ipfs_handler import IPFSHandler
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
    
    def finalize_round(self, round_id):
        print(f"Finalizing round {round_id}...")
        
        nonce = self.blockchain_client.w3.eth.get_transaction_count(self.admin_address)
        
        txn = self.blockchain_client.contract.functions.finalizeRound(round_id).build_transaction({
            'from': self.admin_address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.blockchain_client.w3.eth.gas_price
        })
        
        signed_txn = self.blockchain_client.w3.eth.account.sign_transaction(txn, self.admin_private_key)
        
        tx_hash = self.blockchain_client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        receipt = self.blockchain_client.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"Round {round_id} finalized: {receipt.transactionHash.hex()}")

    def aggregate_and_update(self, round_id):
        print(f"Aggregating and updating model for round {round_id}...")
        
        # Simulate aggregation and update logic here...
    
    def distribute_rewards(self, round_id):
        print(f"Distributing rewards for round {round_id}...")
        
        # Simulate reward distribution logic here...

    def run_federated_learning(self, num_rounds):
        for _ in range(num_rounds):
            self.start_round()
            current_round = self.blockchain_client.get_current_round()
            
            # Get precise end time from blockchain
            round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
            end_time = round_info[1]
            
            # Calculate remaining time
            current_time = int(time.time())
            if current_time < end_time:
                wait_seconds = end_time - current_time
                print(f"Waiting {wait_seconds} seconds for round {current_round}")
                time.sleep(wait_seconds + 1)  # Add buffer
                
            # Force finalization if needed
            if not round_info[2]:
                self.finalize_round(current_round)
                
            self.aggregate_and_update(current_round)
            self.distribute_rewards(current_round)
            print(f"Completed round {current_round}\n{'='*30}")


if __name__ == "__main__":
    blockchain_client = BlockchainClient()
    ipfs_handler = IPFSHandler()
    aggregator = Aggregator()
    
    orchestrator = Orchestrator(blockchain_client, ipfs_handler, aggregator)
    
    print("Starting ZK-FedChain orchestrator...")
    
    orchestrator.run_federated_learning(5)
