# Starting in Regtest

    bitcoind -regtest -daemon

# Create a wallet

    bitcoin-cli -regtest createwallet "testwallet1"

# Create a new address
Keep the address handy for later

    EXAMPLE_ADDR=$(bitcoin-cli -regtest getnewaddress)

# Generate new blocks
(Need at least 100 confirmations)

    bitcoin-cli -regtest generatetoaddress 101 $EXAMPLE_ADDR

# Get balance, show associated UTXOs, spend, generate, and show UTXOs 

    bitcoin-cli -regtest -rpcwallet=testwallet1 getbalance
    bitcoin-cli -regtest -rpcwallet=testwallet1 listunspent
    bitcoin-cli -regtest -named -rpcwallet=testwallet1 sendtoaddress address=<address> amount=30 fee_rate=1
    bitcoin-cli -regtest -rpcwallet=testwallet1 -generate 1
    bitcoin-cli -regtest -rpcwallet=testwallet1 listunspent

