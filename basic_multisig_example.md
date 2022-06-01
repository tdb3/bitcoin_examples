# Creating Individual Wallets
This is just using Core, with Regtest, on the same machine as a simple example.

    bitcoin-cli -regtest -named createwallet wallet_name="ms1_1of3" descriptors=false
    bitcoin-cli -regtest -named createwallet wallet_name="ms1_2of3" descriptors=false
    bitcoin-cli -regtest -named createwallet wallet_name="ms1_3of3" descriptors=false

# Obtaining pubkeys
This relies on Core's ability to fetch info it keeps about generated addresses.

    ADDR1=$(bitcoin-cli -regtest -rpcwallet=ms1_1of3 getnewaddress)
    PUBKEY1=$(bitcoin-cli -regtest -rpcwallet=ms1_1of3 getaddressinfo $ADDR1 | jq -r '.pubkey')
    echo $PUBKEY1

    ADDR2=$(bitcoin-cli -regtest -rpcwallet=ms1_2of3 getnewaddress)
    PUBKEY2=$(bitcoin-cli -regtest -rpcwallet=ms1_2of3 getaddressinfo $ADDR2 | jq -r '.pubkey')
    echo $PUBKEY2

    ADDR3=$(bitcoin-cli -regtest -rpcwallet=ms1_3of3 getnewaddress)
    PUBKEY3=$(bitcoin-cli -regtest -rpcwallet=ms1_3of3 getaddressinfo $ADDR3 | jq -r '.pubkey')
    echo $PUBKEY3

# Creating the multisig address from pubkeys, and a creating a watch-only wallet for it
Creating a P2SH multisig address.

    MS_ADDR_ARRAY=$(bitcoin-cli -regtest -named createmultisig nrequired=2 keys='''["'$PUBKEY1'","'$PUBKEY2'","'$PUBKEY3'"]''')

Save the address, redeemScript, and descriptor.

    MS_ADDR=$(echo $MS_ADDR_ARRAY | jq -r '.address')
    MS_REDEEM_SCRIPT=$(echo $MS_ADDR_ARRAY | jq -r '.redeemScript')
    MS_DESCRIPTOR=$(echo $MS_ADDR_ARRAY | jq -r '.descriptor')

Create a watch-only wallet

    bitcoin-cli -regtest createwallet "multisigwatch" true true 

Import the descriptor from multisig address creation

    bitcoin-cli -regtest -rpcwallet=multisigwatch importdescriptors '[{"desc": "'$MS_DESCRIPTOR'", "timestamp": "now", "label": "ourmultisigaddr"}]'

# Funding the multisig wallet

Send regtest bitcoin to the address.  Example:

    bitcoin-cli -regtest -named -rpcwallet=testwallet1 sendtoaddress address=$MS_ADDR amount=30 fee_rate=1
    bitcoin-cli -regtest -rpcwallet=testwallet1 -generate 1


# Checking balance and transaction details

    bitcoin-cli -regtest -rpcwallet=multisigwatch getbalance
    MS_FUNDING_TXID=$(bitcoin-cli -regtest -rpcwallet=multisigwatch listtransactions | jq -r '.[0].txid')
    MS_FUNDING_TX_DETAILS=$(bitcoin-cli -regtest -rpcwallet=multisigwatch gettransaction $MS_FUNDING_TXID true true)
    echo $MS_FUNDING_TX_DETAILS | jq

Find the appropriate vout (e.g., 0, which pays to our multisig address) from the transaction details, and save info from it.

    MS_FUNDING_VOUT=0
    MS_FUNDING_SPK=$(echo $MS_FUNDING_TX_DETAILS | jq -r ".decoded.vout[$MS_FUNDING_VOUT].scriptPubKey.hex")

# Spending the UTXO

Create a raw transaction using the UTXO (and VOUT of 0).  
Recipient will be a new address in testwallet1.  
Fee is implied from the UTXO amount (30) minus the amount being sent (29.9999).

    RECIPIENT_ADDR=$(bitcoin-cli -regtest -rpcwallet=testwallet1 getnewaddress)

    NEWTXHEX=$(bitcoin-cli -regtest -rpcwallet=multisigwatch -named createrawtransaction inputs='''[ { "txid": "'$MS_FUNDING_TXID'", "vout": '$MS_FUNDING_VOUT' } ]''' outputs='''{ "'$RECIPIENT_ADDR'": 29.9999}''')

Need two of three signatures.  First:

Fetch the privkey of the first signer, and use to sign the transaction.

    PRIVKEY1=$(bitcoin-cli -regtest -rpcwallet=ms1_1of3 dumpprivkey $ADDR1)

    NEWTXHEX_AFTERSIG1=$(bitcoin-cli -regtest -rpcwallet=ms1_1of3 -named signrawtransactionwithkey hexstring=$NEWTXHEX prevtxs='''[ { "txid": "'$MS_FUNDING_TXID'", "vout": '$MS_FUNDING_VOUT', "scriptPubKey": "'$MS_FUNDING_SPK'", "redeemScript": "'$MS_REDEEM_SCRIPT'" } ]''' privkeys='["'$PRIVKEY1'"]' | jq -r ".hex")

    unset PRIVKEY1


Fetch the privkey of the second signer, and use to sign the transaction.

    PRIVKEY3=$(bitcoin-cli -regtest -rpcwallet=ms1_3of3 dumpprivkey $ADDR3)

    NEWTXHEX_THRESHOLD_REACHED=$(bitcoin-cli -regtest -rpcwallet=ms1_3of3 -named signrawtransactionwithkey hexstring=$NEWTXHEX_AFTERSIG1 prevtxs='''[ { "txid": "'$MS_FUNDING_TXID'", "vout": '$MS_FUNDING_VOUT', "scriptPubKey": "'$MS_FUNDING_SPK'", "redeemScript": "'$MS_REDEEM_SCRIPT'" } ]''' privkeys='["'$PRIVKEY3'"]' | jq -r ".hex")

    unset PRIVKEY3

Send the signed transaction, generate a block to confirm it, and check balances.

    bitcoin-cli -regtest -rpcwallet=ms1_3of3 sendrawtransaction $NEWTXHEX_THRESHOLD_REACHED
    bitcoin-cli -regtest -rpcwallet=testwallet1 -generate 1
    bitcoin-cli -regtest -rpcwallet=multisigwatch getbalance
    bitcoin-cli -regtest -rpcwallet=testwallet1 getbalance
    
The multisig wallet should show zero balance, and the recipient should have 29.9999 more regtest btc (in addition to the 50 btc block reward).
