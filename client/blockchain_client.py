import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class BlockchainClient:
    def __init__(self, node_url=None, contract_address=None):
        self.w3 = Web3(Web3.HTTPProvider(
            node_url or os.getenv('ETHEREUM_NODE_URL', 'http://localhost:7545')
        ))
        
        with open('build/contracts/FedChainCore.json') as f:
            contract_data = json.load(f)
            self.contract_abi = contract_data['abi']
        
        self.contract_address = contract_address or os.getenv('CONTRACT_ADDRESS')
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

    def get_current_round(self):
        return self.contract.functions.roundId().call()

    def submit_gradient(self, address, private_key, round_id, gradient_ipfs_hash, zk_proof, public_inputs):
        nonce = self.w3.eth.get_transaction_count(address)
        
        proof_bytes = Web3.to_bytes(hexstr=zk_proof)
        inputs_bytes = Web3.to_bytes(hexstr=public_inputs)
        
        txn = self.contract.functions.submitGradient(
            round_id,
            gradient_ipfs_hash,
            proof_bytes,
            inputs_bytes
        ).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)
