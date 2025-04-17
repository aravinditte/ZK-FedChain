import argparse
import os
import time
import json
from dotenv import load_dotenv
from web3 import Web3

from client.data_handler import DataHandler
from client.model_trainer import ModelTrainer
from client.zk_prover import ZKProver
from client.blockchain_client import BlockchainClient
from server.ipfs_handler import IPFSHandler

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='ZK-FedChain Client Node')
    parser.add_argument('--participant-id', type=int, required=True, help='Participant ID')
    parser.add_argument('--private-key', type=str, required=True, help='Private key for blockchain transactions')
    parser.add_argument('--data-path', type=str, default='data', help='Path to training data')
    
    args = parser.parse_args()
    
    # Initialize components
    data_handler = DataHandler(args.data_path)
    model_trainer = ModelTrainer()
    zk_prover = ZKProver()
    blockchain_client = BlockchainClient()
    ipfs_handler = IPFSHandler()
    
    # Get participant address from private key
    w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_NODE_URL', 'http://localhost:7545')))
    account = w3.eth.account.from_key(args.private_key)
    participant_address = account.address
    
    print(f"Starting client node for participant {args.participant_id} ({participant_address})")
    
    # Register participant if not already registered
    try:
        participant_info = blockchain_client.contract.functions.participants(participant_address).call()
        if not participant_info[0]:  # isRegistered
            print("Registering participant...")
            
            # Approve token spending first
            token_address = blockchain_client.contract.functions.fedToken().call()
            token_contract = w3.eth.contract(
                address=token_address,
                abi=json.load(open('build/contracts/FedToken.json'))['abi']
            )
            
            # Approve tokens
            nonce = w3.eth.get_transaction_count(participant_address)
            txn = token_contract.functions.approve(
                blockchain_client.contract_address,
                100 * 10**18  # 100 tokens
            ).build_transaction({
                'from': participant_address,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_txn = w3.eth.account.sign_transaction(txn, args.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Register
            blockchain_client.register_participant(participant_address, args.private_key)
            print("Registration successful!")
        else:
            print("Participant already registered")
    except Exception as e:
        print(f"Error during registration: {e}")
        return
    
    # Load and preprocess data
    print("Loading and preprocessing data...")
    data_handler.load_data()
    data_handler.preprocess_data()
    
    # Main loop - participate in training rounds
    while True:
        try:
            # Get current round
            current_round = blockchain_client.get_current_round()
            round_info = blockchain_client.contract.functions.rounds(current_round).call()
            
            # Check if already submitted for this round
            has_submitted = blockchain_client.contract.functions.rounds(current_round).call()[participant_address]
            
            if has_submitted:
                print(f"Already submitted for round {current_round}, waiting for next round...")
                time.sleep(60)  # Check again in 1 minute
                continue
            
            # Check if round is still active
            if int(time.time()) > round_info[1]:  # endTime
                print(f"Round {current_round} has ended, waiting for next round...")
                time.sleep(60)  # Check again in 1 minute
                continue
            
            print(f"Participating in round {current_round}...")
            
            # Get current model
            current_model_hash = blockchain_client.get_current_model()
            
            # If model exists, load it
            if current_model_hash and current_model_hash != "":
                try:
                    model_weights = ipfs_handler.get_json(current_model_hash)
                    model_trainer.set_weights(model_weights)
                    print(f"Loaded model from IPFS: {current_model_hash}")
                except Exception as e:
                    print(f"Error loading model: {e}")
                    # Continue with default model
            
            # Train locally
            x_train, y_train = data_handler.get_train_data()
            print("Training local model...")
            model_trainer.train(x_train, y_train, epochs=1)
            
            # Evaluate
            x_test, y_test = data_handler.get_test_data()
            loss, accuracy = model_trainer.evaluate(x_test, y_test)
            print(f"Local model evaluation - Loss: {loss}, Accuracy: {accuracy}")
            
            # Compute gradients
            print("Computing gradients...")
            gradients = model_trainer.get_gradients(x_train[:32], y_train[:32])
            
            # Generate ZK proof
            print("Generating ZK proof...")
            proof, public_inputs = zk_prover.generate_gradient_proof(gradients)
            
            # Save gradients to IPFS
            print("Saving gradients to IPFS...")
            gradients_list = [g.tolist() for g in gradients]
            gradient_hash = ipfs_handler.add_json(gradients_list)
            print(f"Gradients saved to IPFS: {gradient_hash}")
            
            # Submit to blockchain
            print("Submitting to blockchain...")
            blockchain_client.submit_gradient(
                participant_address,
                args.private_key,
                current_round,
                gradient_hash,
                bytes.fromhex(proof[2:]),  # Remove 0x prefix
                bytes.fromhex(public_inputs[2:])  # Remove 0x prefix
            )
            
            print(f"Successfully submitted gradient for round {current_round}")
            
            # Wait for next round
            time.sleep(round_info[1] - int(time.time()) + 60)  # Wait until end of round + 1 minute
            
        except Exception as e:
            print(f"Successfully submitted gradient for round {current_round}")
            
            # Wait for next round
            time.sleep(round_info[1] - int(time.time()) + 60)  # Wait until end of round + 1 minute
            
        except Exception as e:
            print(f"Error during training round: {e}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    main()