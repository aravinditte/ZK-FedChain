import os
import time
import json
from web3 import Web3
from client.blockchain_client import BlockchainClient
from client.zk_prover import ZKProver

def simulate_participant(participant_address, private_key):
    bc = BlockchainClient()
    zk = ZKProver()
    
    print("\n=== Participant Simulation ===")
    
    # Get current round before any actions
    initial_round = bc.get_current_round()
    print(f"Initial Round: {initial_round}")
    
    # Check registration
    is_registered = bc.contract.functions.participants(participant_address).call()[0]
    
    if not is_registered:
        print("\n[1/3] Registering Participant...")
        
        # Approve tokens
        token_address = bc.contract.functions.fedToken().call()
        with open('build/contracts/FedToken.json') as f:
            token_abi = json.load(f)['abi']
        
        token_contract = bc.w3.eth.contract(address=token_address, abi=token_abi)
        
        approve_txn = token_contract.functions.approve(
            bc.contract_address,
            100 * 10**18
        ).build_transaction({
            'from': participant_address,
            'nonce': bc.w3.eth.get_transaction_count(participant_address),
            'gas': 200000,
            'gasPrice': bc.w3.eth.gas_price
        })
        
        signed_approve = bc.w3.eth.account.sign_transaction(approve_txn, private_key)
        bc.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
        print("Tokens approved")
        time.sleep(15)
        
        # Register
        print("[2/3] Registering...")
        register_receipt = bc.register_participant(participant_address, private_key)
        print(f"Registration Tx: {register_receipt.transactionHash.hex()}")
        time.sleep(15)
    
    # Submit gradient
    current_round = bc.get_current_round()
    round_info = bc.contract.functions.rounds(current_round).call()
    
    if time.time() > round_info[1]:
        print(f"Round {current_round} has ended. Waiting for new round...")
        return
    
    print(f"\n[3/3] Submitting to CURRENT ROUND {current_round}")
    
    proof, inputs = zk.generate_gradient_proof([])
    receipt = bc.submit_gradient(
        participant_address,
        private_key,
        current_round,
        "Qmdummyhash",
        proof,
        inputs
    )
    print(f"\nSubmission Successful!")
    print(f"Tx Hash: {receipt.transactionHash.hex()}")
    print(f"Block Number: {receipt.blockNumber}")

if __name__ == "__main__":
    admin_address = os.getenv('ADMIN_ADDRESS')
    admin_private_key = os.getenv('ADMIN_PRIVATE_KEY')
    
    if not admin_address or not admin_private_key:
        raise ValueError("Missing ADMIN_ADDRESS or ADMIN_PRIVATE_KEY in .env")
    
    simulate_participant(admin_address, admin_private_key)
