# client/blockchain_client.py
import os
import json
from web3 import Web3
from dotenv import load_dotenv

class BlockchainClient:
    def __init__(self, node_url=None, contract_address=None, abi_path=None):
        # Load environment variables
        load_dotenv()
        
        # Get absolute path to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set default ABI path
        if not abi_path:
            abi_path = os.path.join(
                project_root, 
                'build', 
                'contracts', 
                'FedChainCore.json'
            )

        # Load contract ABI
        try:
            with open(abi_path, 'r') as abi_file:
                contract_data = json.load(abi_file)
                self.contract_abi = contract_data['abi']
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Contract ABI not found at {abi_path}. "
                "Make sure you've compiled contracts with 'truffle compile'"
            )

        # Initialize Web3
        self.node_url = node_url or os.getenv('ETHEREUM_NODE_URL', 'http://localhost:8545')
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        
        # Get contract address
        self.contract_address = contract_address or os.getenv('CONTRACT_ADDRESS')
        if not self.contract_address:
            raise ValueError("Contract address not provided and not found in .env")
        
        # Create contract instance
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )

    def register_participant(self, address, private_key):
        nonce = self.w3.eth.get_transaction_count(address)
        txn = self.contract.functions.register().build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def submit_gradient(self, address, private_key, round_id, gradient_ipfs_hash, zk_proof, public_inputs):
        nonce = self.w3.eth.get_transaction_count(address)
        txn = self.contract.functions.submitGradient(
            round_id, 
            gradient_ipfs_hash, 
            zk_proof, 
            public_inputs
        ).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def get_current_round(self):
        return self.contract.functions.roundId().call()

    def get_current_model(self):
        return self.contract.functions.currentModelIpfsHash().call()
