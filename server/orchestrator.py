import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from web3 import Web3
from client.blockchain_client import BlockchainClient
from server.ipfs_handler import IPFSHandler
from server.aggregator import Aggregator

load_dotenv()

class Orchestrator:
    def __init__(self, blockchain_client, ipfs_handler, aggregator):
        self.blockchain_client = blockchain_client
        self.ipfs_handler = ipfs_handler
        self.aggregator = aggregator
        self.admin_address = os.getenv('ADMIN_ADDRESS')
        self.admin_private_key = os.getenv('ADMIN_PRIVATE_KEY')
        self.min_participants = self.blockchain_client.contract.functions.minParticipants().call()

    def start_round(self):
        current_round = self.blockchain_client.get_current_round()
        current_model = self.blockchain_client.get_current_model()
        print(f"\n=== Starting Round {current_round} ===")
        print(f"Initial Model: {current_model}")
        print(f"Target Participants: {self.min_participants}")

    def finalize_round(self, round_id):
        print(f"\nFinalizing Round {round_id}...")
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
        print(f"Finalized! Block: {receipt.blockNumber}")

    def run_federated_learning(self, num_rounds):
        for _ in range(num_rounds):
            current_round = self.blockchain_client.get_current_round()
            round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
            
            # Initialize new round if needed
            if round_info[0] == 0:
                self.start_round()
                current_round = self.blockchain_client.get_current_round()
                round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
    
            start_time = round_info[0]
            end_time = round_info[1]
            participant_count = round_info[4]
            
            print(f"\n=== Round {current_round} ===")
            print(f"Start: {start_time} | End: {end_time}")
            print(f"Participants: {participant_count}/{self.min_participants}")
    
            # Active monitoring
            while time.time() < end_time and participant_count < self.min_participants:
                print(f"Waiting... (Remaining: {int(end_time - time.time())}s)")
                time.sleep(15)
                round_info = self.blockchain_client.contract.functions.rounds(current_round).call()
                participant_count = round_info[4]
    
            # Finalization logic
            if participant_count >= self.min_participants:
                self.finalize_round(current_round)
            else:
                print(f"Round {current_round} ended without enough participants")
            
            print(f"=== Completed Round {current_round} ===\n{'='*40}")


if __name__ == "__main__":
    bc = BlockchainClient()
    ipfs = IPFSHandler()
    aggregator = Aggregator()
    
    orchestrator = Orchestrator(bc, ipfs, aggregator)
    orchestrator.run_federated_learning(5)
