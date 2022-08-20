from buidl.tx import TxFetcher

txid = "5297eb50852bda794dfd7cdd338ed815e448191811a0608140913c98e80817ae"
print("Attempting to fetch " + txid)

tx = TxFetcher.fetch(txid, network="testnet")
print("Fetched.  Printing")

print(tx)

print("Using methods")
print("txid: " + tx.id())
print("fee: " + str(tx.fee()))
print("inputs: ")
for ti in tx.tx_ins:
    print("  prev_txid: " + ti.prev_tx.hex())
    print("  index: " + str(ti.prev_index))
print("outputs: ")
for to in tx.tx_outs:
    print("  amount: " + str(to.amount))
    print("  spk: " + str(to.script_pubkey))

print("\nserialized: " + tx.serialize().hex())

print("\nGetting OP_RETURN data: " + tx.tx_outs[1].script_pubkey.commands[1].hex())
