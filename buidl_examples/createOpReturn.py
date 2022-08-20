from buidl.script import Script

print("Creating OP_RETURN")
scr = Script([106, "some data".encode()])

print("Commands within Script:")
for c in scr.commands:
    print("  command: " + str(c))

print("Script serialized (including leading size): " + scr.serialize().hex())
print("Script serialized (without leading size): " + scr.raw_serialize().hex())
