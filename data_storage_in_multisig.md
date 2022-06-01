# Data Storage in Multisig 
A relatively simple way to store aribrary data (other than OP_RETURN) is to take advantage of threshold multisig in bitcoin.  
Since the redeem script used in a P2SH multisig spend includes all pubkeys part of the multisig address (embedded in the script), one or more of the pubkeys can be sacrificed to store arbitrary data rather than the public key of a signer.  

There are limitations to this data storage method.  
For example, the data would need to be at most the size of a pubkey (e.g., 32 bytes for SEC compressed pubkeys, if the first byte indicating y type is excluded for data storage), the data would need to be a valid X-point on the secp256k1 eliptic curve ($y^2 = x^3 + 7$) and fit the characteristics of secp256k1 (e.g., order).  
Also, since one ore more of the pubkeys are being used for data storage (for which we are unlikely to control the cooresponding private key), these keys reduce the redundancy of the multisg.  For example, a 2 of 3 multisig would effectively become a 2 of 2 multisig if one of the pubkeys was used for data storage.

> **_NOTE:_** One of the differences between storing data in a threshold multisig vs an OP_RETURN is that OP_RETURNs are excluded from the UTXO set, and less data in the UTXO set is friendlier to scalability.

# Example with Bitcoin Core
## Creating wallets
    bitcoin-cli -regtest -named createwallet wallet_name="msdata_1of3" descriptors=false
    bitcoin-cli -regtest -named createwallet wallet_name="msdata_2of3" descriptors=false

## Obtaining pubkeys
### Obtaining normal pubkeys
    ADDR1=$(bitcoin-cli -regtest -rpcwallet=msdata_1of3 getnewaddress)
    PUBKEY1=$(bitcoin-cli -regtest -rpcwallet=msdata_1of3 getaddressinfo $ADDR1 | jq -r '.pubkey')
    echo $PUBKEY1

    ADDR2=$(bitcoin-cli -regtest -rpcwallet=msdata_2of3 getnewaddress)
    PUBKEY2=$(bitcoin-cli -regtest -rpcwallet=msdata_2of3 getaddressinfo $ADDR2 | jq -r '.pubkey')
    echo $PUBKEY2

### Create the data and masquerade it as a pubkey

    X_PAD=$(printf "%0.s0" {1..64})
    UNPADDED_DATA=$(echo -n "Some arbitrary data" | xxd -p)
    DATAPUBKEY=$(printf "02%s\n" "${X_PAD:${#UNPADDED_DATA}}$UNPADDED_DATA")
    echo $DATAPUBKEY

## Creating the multisig address from pubkeys, creating a watch-only wallet, funding the multisig, and checking the balance
Follow [Basic Multisig Example](basic_multisig_example.md) to fund the multisig and spend from it.

## View the data
Get the transaction details

    TX_DETAILS=$(bitcoin-cli -regtest -rpcwallet=testwallet1 gettransaction c903ed06abe5af8dc942902cd6c5df996297890034d20c79e8270a0690efb024)

Where `c903ed06abe5af8dc942902cd6c5df996297890034d20c79e8270a0690efb024` is the txid of the transaction that spent from the multisig.  

Fetch the script (assembly view) used to spend the transaction, which includes our data pubkey, interpret as ascii and show.

    TX_SCRIPT_ASM=$(bitcoin-cli -regtest -rpcwallet=testwallet1 decoderawtransaction $(echo $TX_DETAILS | jq -r ".hex") | jq -r ".vin[0].scriptSig.asm")
    SCRIPT_MINUS_SIGS=$(echo $TX_SCRIPT_ASM | rev | cut -d' ' -f 1 | rev)
    RETRIEVED_DATAPUBKEY=$(bitcoin-cli -regtest -rpcwallet=testwallet1 decodescript $SCRIPT_MINUS_SIGS | jq -r ".asm" | cut -d' ' -f 4)
    echo "${RETRIEVED_DATAPUBKEY:2}" | xxd -r -p; echo ""

