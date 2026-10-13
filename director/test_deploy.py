import os
import solcx

from web3 import Web3
from web3 import HTTPProvider

SOLIDITY_VERSION = "0.8.18"
CONTRACT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solidity", "OrderVoting.sol")

web3 = Web3(HTTPProvider("http://localhost:8545"))

print("Povezan:", web3.is_connected())
print("Nalozi:", len(web3.eth.accounts))

with open(CONTRACT_PATH, "r") as file:
    source = file.read()

compiled = solcx.compile_source(source, output_values = ["abi", "bin"], solc_version = SOLIDITY_VERSION)

for name, data in compiled.items():
    if name.endswith(":OrderVoting"):
        abi = data["abi"]
        bytecode = data["bin"]

voters = web3.eth.accounts[1:4] # tri glasaca

contract = web3.eth.contract(abi = abi, bytecode = bytecode)
transaction_hash = contract.constructor(voters).transact({"from": web3.eth.accounts[0]})
receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

address = receipt.contractAddress
print("Ugovor postavljen na:", address)

contract = web3.eth.contract(address = address, abi = abi)
print("Stanje pre glasanja:", contract.functions.get_state().call())

contract.functions.approve().transact({"from": voters[0]})
print("Posle prvog glasa:", contract.functions.get_state().call())

contract.functions.approve().transact({"from": voters[1]})
print("Posle drugog glasa:", contract.functions.get_state().call())

print("Podaci za transakciju:", contract.encodeABI(fn_name = "approve"))