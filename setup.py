import os
import json
import subprocess
import argparse
import sys
from web3 import Web3
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description='ZK-FedChain Setup Script')
    parser.add_argument('--deploy', action='store_true', help='Deploy contracts')
    parser.add_argument('--setup-env', action='store_true', help='Set up environment variables')
    args = parser.parse_args()
    
    if args.deploy:
        deploy_contracts()
    
    if args.setup_env:
        setup_environment()

def deploy_contracts():
    print("Deploying contracts...")
    try:
        # Use npx to run truffle - this works regardless of installation method
        migrate_cmd = ["npx", "truffle", "migrate", "--reset", "--network", "development"]
        print(f"Running command: {' '.join(migrate_cmd)}")
        
        # Change directory to contracts when running the command
        cwd = "contracts"
            
        result = subprocess.run(
            migrate_cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            shell=True  # Use shell on Windows to find npx
        )
        
        print(result.stdout)
        
        # Extract contract addresses from output
        lines = result.stdout.split('\n')
        fed_token_address = None
        model_nft_address = None
        zk_verifier_address = None
        fed_chain_core_address = None
        
        for line in lines:
            if "FedToken deployed at:" in line:
                fed_token_address = line.split("at: ")[1].strip()
            elif "ModelNFT deployed at:" in line:
                model_nft_address = line.split("at: ")[1].strip()
            elif "ZKVerifier deployed at:" in line:
                zk_verifier_address = line.split("at: ")[1].strip()
            elif "FedChainCore deployed at:" in line:
                fed_chain_core_address = line.split("at: ")[1].strip()
        
        print("\nDeployed contract addresses:")
        print(f"FedToken: {fed_token_address}")
        print(f"ModelNFT: {model_nft_address}")
        print(f"ZKVerifier: {zk_verifier_address}")
        print(f"FedChainCore: {fed_chain_core_address}")
        
        # Save addresses to a file
        with open('contract_addresses.json', 'w') as f:
            json.dump({
                'FedToken': fed_token_address,
                'ModelNFT': model_nft_address,
                'ZKVerifier': zk_verifier_address,
                'FedChainCore': fed_chain_core_address
            }, f, indent=2)
        
        print("\nContract addresses saved to contract_addresses.json")
        
        return fed_chain_core_address
        
    except subprocess.CalledProcessError as e:
        print(f"Error deploying contracts: {e}")
        if e.stderr:
            print(e.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def setup_environment():
    print("Setting up environment variables...")
    
    # Load existing .env file if it exists
    env_vars = {}
    if os.path.exists('.env'):
        load_dotenv()
        for key in ['ETHEREUM_NODE_URL', 'CONTRACT_ADDRESS', 'ADMIN_ADDRESS', 'ADMIN_PRIVATE_KEY', 'IPFS_API_URL']:
            if os.getenv(key):
                env_vars[key] = os.getenv(key)
    
    # Connect to Ethereum node
    ethereum_node_url = env_vars.get('ETHEREUM_NODE_URL', 'http://localhost:8545')
    w3 = Web3(Web3.HTTPProvider(ethereum_node_url))
    
    try:
        if not w3.is_connected():
            print(f"Warning: Could not connect to Ethereum node at {ethereum_node_url}")
            print("Continuing setup, but please ensure your Ethereum node is running.")
    except Exception as e:
        print(f"Warning: Error connecting to Ethereum node: {e}")
        print("Continuing setup, but please ensure your Ethereum node is running.")
    
    # Get contract address from file or user input
    contract_address = env_vars.get('CONTRACT_ADDRESS')
    if not contract_address:
        if os.path.exists('contract_addresses.json'):
            with open('contract_addresses.json', 'r') as f:
                addresses = json.load(f)
                contract_address = addresses.get('FedChainCore')
        
        if not contract_address:
            contract_address = input("Enter FedChainCore contract address: ")
    
    # Get admin address and private key
    admin_address = env_vars.get('ADMIN_ADDRESS')
    if not admin_address:
        try:
            admin_address = w3.eth.accounts[0]
        except:
            admin_address = input("Enter admin address: ")
    
    admin_private_key = env_vars.get('ADMIN_PRIVATE_KEY')
    if not admin_private_key:
        admin_private_key = input("Enter admin private key (without 0x prefix): ")
        if not admin_private_key.startswith('0x'):
            admin_private_key = '0x' + admin_private_key
    
    # Get IPFS API URL
    ipfs_api_url = env_vars.get('IPFS_API_URL', '/ip4/127.0.0.1/tcp/5001')
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write(f"ETHEREUM_NODE_URL={ethereum_node_url}\n")
        f.write(f"CONTRACT_ADDRESS={contract_address}\n")
        f.write(f"ADMIN_ADDRESS={admin_address}\n")
        f.write(f"ADMIN_PRIVATE_KEY={admin_private_key}\n")
        f.write(f"IPFS_API_URL={ipfs_api_url}\n")
    
    print("Environment variables set up successfully!")
    print(f"Ethereum Node: {ethereum_node_url}")
    print(f"Contract Address: {contract_address}")
    print(f"Admin Address: {admin_address}")
    print(f"IPFS API URL: {ipfs_api_url}")

if __name__ == "__main__":
    main()
