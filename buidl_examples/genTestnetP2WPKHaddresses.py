from buidl import *

# Ask the user how many addresses they would like to generate
print("Will generate P2WPKH addresses from mnemonic.  Testnet is used")
bnet = "testnet"
mnemonic = input("Enter mnemonic (space separated): ")
num_addresses = int(input("Number of addresses to generate: "))
starting_address_index = int(input("Starting address index for external (non-change) addresses: "))

hd_priv = HDPrivateKey.from_mnemonic(mnemonic=mnemonic, network=bnet)

print("\nReceiving addresses (" + str(starting_address_index) + " to " + str(starting_address_index+num_addresses) + "): ")
for i in range(num_addresses):
    print(hd_priv.get_p2wpkh_receiving_address(address_num=(starting_address_index+i)))

print("\nChange addresses (0 to " + str(num_addresses) + "): ")
for i in range(num_addresses):
    print(hd_priv.get_p2wpkh_change_address(address_num=i))
