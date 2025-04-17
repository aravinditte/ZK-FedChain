from web3 import Web3
import os

w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
print(f"Connected to node: {w3.is_connected()}")

contract_address = "YOUR_CONTRACT_ADDRESS"  # From truffle migrate output
contract_code = w3.eth.get_code(contract_address)
print(f"Contract code length: {len(contract_code)} bytes")
