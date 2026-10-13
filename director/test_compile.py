import os
import solcx

SOLIDITY_VERSION = "0.8.18"
CONTRACT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solidity", "OrderVoting.sol")

solcx.install_solc(SOLIDITY_VERSION)

with open(CONTRACT_PATH, "r") as file:
    source = file.read()

compiled = solcx.compile_source(
    source,
    output_values = ["abi", "bin"],
    solc_version = SOLIDITY_VERSION
)

for name, data in compiled.items():
    print("NAZIV:", name)
    print("BYTECODE duzina:", len(data["bin"]))
    print("FUNKCIJE:", [item.get("name") for item in data["abi"] if item.get("type") == "function"])