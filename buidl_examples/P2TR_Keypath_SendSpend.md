# P2TR Basic Single Sig Keypath Send/Spend Example
Quick example to spend from a P2WPKH UTXO to a P2TR address (which is constructed for basic single-sig keypath spend),
then spend that P2TR UTXO to another P2TR address.

In this example, for simplicity, the spending is to/from keys derived from the same HD seed.
The P2WPKH UTXO that already has tBTC is associated with HD key m/84'/1'/0'/0/0 (1st receiving P2WPKH addresss).

## Spend from P2WPKH UTXO to P2TR address

Spend from m/84'/1'/0'/0/0 to m/86'/1'/0'/0/0 (1st receiving key, used for basic single-sig P2TR key path).

Imports and HD key instantiation:
```
>>> from buidl.hd import HDPrivateKey
>>> from buidl.tx import TxIn,TxOut,Tx,TxFetcher
>>> from buidl.taproot import TapRoot
>>> phrase = "your seed phrase here ... e.g., 24 words space separated in a quoted string"
>>> hd_priv = HDPrivateKey.from_mnemonic(mnemonic=phrase, network="testnet")
```
Generate the associated P2TR address to which we spend the P2WPKH UTXO:
```
>>> tr_internal_priv_key = hd_priv.traverse("m/86h/1h/0h/0/0").private_key
>>> tr_internal_pub_key = tr_internal_priv_key.point
>>> tap_root = TapRoot(tr_internal_pub_key)
>>> p2tr_addr = tap_root.address(network="testnet")
>>> print(p2tr_addr) # This is the P2TR address to which we spend the P2WPKH UTXO
```
Build, sign, and broadcast the transaction to spend the P2WPKH UTXO to the P2TR address:
```
>>> utxo1_txid = "txid associated with the utxo in a quoted string"
>>> utxo1_index = 0 # appropriate output index associated with the UTXO
>>> tx1_in = TxIn(bytes.fromhex(utxo1_txid), utxo1_index) # Buid the 
>>> fee = 500
>>> amount1 = tx1_in.value(network="testnet") - fee
>>> tx1_out = TxOut.to_address(p2tr_addr, amount1)
>>> tx1 = Tx(1, [tx1_in], [tx1_out], 0, network="testnet", segwit=True)
>>> p2wpkh_key = hd_priv.traverse("m/84h/1h/0h/0/0").private_key # note the 84 vs 86, see BIPs 84 and 86 for further details
>>> tx1.sign_input(0, p2wpkh_key)
True
>>> utxo2_txid = TxFetcher.sendrawtransaction(tx1.serialize().hex(), network="testnet")
```
## Spend from P2TR UTXO to another P2TR address

Spend from m/86'/1'/0'/0/0 to m/86'/1'/0'/1/0 (1st change key, used for basic single-sig P2TR key path).

After confirmation, generate the next P2TR address to which we spend the first P2TR UTXO:
```
>>> tr_internal_priv_key2 = hd_priv.traverse("m/86h/1h/0h/1/0").private_key  # First change address
>>> tr_internal_pub_key2 = tr_internal_priv_key2.point
>>> tap_root2 = TapRoot(tr_internal_pub_key2)
>>> p2tr_addr2 = tap_root2.address(network="testnet")
>>> print(p2tr_addr2) # The next P2TR address
```
Build, sign, and broadcast the transaction to spend the first P2TR UTXO to the second P2TR address:
```
>>> utxo2_index = 0
>>> tx2_in = TxIn(bytes.fromhex(utxo2_txid), utxo2_index)
>>> amount2 = tx2_in.value(network="testnet") - fee
>>> tx2_out = TxOut.to_address(p2tr_addr2, amount2)
>>> tx2 = Tx(1, [tx2_in], [tx2_out], 0, network="testnet", segwit=True)
>>> tweaked_privkey = tr_internal_priv_key.tweaked(tap_root.tweak)  # create the tweaked private key, to sign
>>> tx2.sign_input(0, tweaked_privkey)
>>> final_txid = TxFetcher.sendrawtransaction(tx2.serialize().hex(), network="testnet")
>>> print(final_txid)
```
