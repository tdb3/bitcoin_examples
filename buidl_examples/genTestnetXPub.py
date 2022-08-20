from buidl.hd import HDPrivateKey

print("Will generate the xpub from a private mnemonic. Uses testnet3.")

bnet = "testnet"
mnemonic = input("Enter the 24-word mnemonic (space separated): ")

hd_priv = HDPrivateKey.from_mnemonic(mnemonic=mnemonic, network=bnet)
xpub = hd_priv.xpub()
print(xpub)
