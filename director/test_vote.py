from web3 import Web3
from web3 import HTTPProvider

web3 = Web3(HTTPProvider("http://localhost:8545"))

contract_address = "0x388a761A65b4493cDFea825E6a4Df79029DfbD9A"
approve_data = "0x12424e3f"

voter1 = "0x7f632541C657C2C7798b5EA22e8154d99785609e"
voter2 = "0xDf52182cc254a55e8151b5bA7cADB2Db2491d0A1"

web3.eth.send_transaction({
    "from": voter1,
    "to": contract_address,
    "data": approve_data,
    "gas": 100000
})
print("Glas 1 poslan")

web3.eth.send_transaction({
    "from": voter2,
    "to": contract_address,
    "data": approve_data,
    "gas": 100000
})
print("Glas 2 poslan")