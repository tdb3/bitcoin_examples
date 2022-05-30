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
    bitcoin-cli -regtest getbalance

