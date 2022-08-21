from buidl.hd import HDPrivateKey

# Ask the user how many addresses they would like to generate
print("Will generate simple single sig P2TR keypath addresses from mnemonic.  Testnet is used.")
bnet = "testnet"
mnemonic = input("Enter mnemonic (space separated, e.g. 24 words): ")
num_addresses = int(input("Number of addresses to generate: "))
starting_address_index = int(input("Starting address index for external (non-change) addresses: "))

hd_priv = HDPrivateKey.from_mnemonic(mnemonic=mnemonic, network=bnet)

print("\nReceiving addresses (" + str(starting_address_index) + " to " + str(starting_address_index+num_addresses) + "): ")
for i in range(num_addresses):
    print(hd_priv.traverse("m/86h/1h/0h/0/" + str(starting_address_index+i)).p2tr_address())


print("\nChange addresses (0 to " + str(num_addresses) + "): ")
for i in range(num_addresses):
    print(hd_priv.traverse("m/86h/1h/0h/1/" + str(i)).p2tr_address())
