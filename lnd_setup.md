# Creating LND Node
This is meant for familiarization only (non-production and not fund-handling).

## Create the initial container/VM

4GB RAM, 20GB storage, Ubuntu 22.04 or Debian 12

### Update

```
apt update
apt full-upgrade
apt install gnupg curl wget tmux
reboot
```

## LND Installation Notes
This lnd node was installed onto a different container/VM than the Bitcoin Core node with which it communicates.  The node is accessed over a local subnet, so lnd conf settings are set to facilitate this accordingly (and a new rpcauth line is used in bitcoin.conf).


## Add Network Interface to Local Node Network
Power off.
Add network interface to node network.
Power on.
Verify communication between the lnd VM/container and the bitcoind node.


## Obtain LND

Based on steps in:
https://raspibolt.org/guide/lightning/lightning-client.html

and on LND github page's release info:
https://github.com/lightningnetwork/lnd/releases

Loosely followed:
https://youtu.be/UMXS7u4RHwI

(check that the latest version of lnd is being used, not 0.16.2)
As root:
```
mkdir lndDownloads
cd lndDownloads
wget https://github.com/lightningnetwork/lnd/releases/download/v0.16.2-beta/lnd-linux-amd64-v0.16.2-beta.tar.gz
wget https://github.com/lightningnetwork/lnd/releases/download/v0.16.2-beta/manifest-v0.16.2-beta.txt
wget https://github.com/lightningnetwork/lnd/releases/download/v0.16.2-beta/manifest-roasbeef-v0.16.2-beta.sig
wget https://github.com/lightningnetwork/lnd/releases/download/v0.16.2-beta/manifest-roasbeef-v0.16.2-beta.sig.ots
```

Verify signature:
```
sha256sum --check manifest-v0.16.2-beta.txt --ignore-missing
curl https://raw.githubusercontent.com/lightningnetwork/lnd/master/scripts/keys/roasbeef.asc | gpg --import
gpg --verify manifest-roasbeef-v0.16.2-beta.sig manifest-v0.16.2-beta.txt
```

On another machine, download and hash (```sha256sum```) the files ```manifest-roasbeef-v0.16.2-beta.sig``` and ```manifest-roasbeef-v0.16.2-beta.sig.ots```.  Hash on the server and ensure the hashes match.

Access https://opentimestamps.org/ Stamp and Verify section.
Drag the ots file into the web interface, followed by the sig file.
Ensure verification is correct (e.g. ```Bitcoin block 787408 attests existence as of 2023-04-28 EST```).
Check that the date is close to the release date of the LND binary (should be same day).


## Install LND

```
tar xzf lnd-linux-amd64-v0.16.2-beta.tar.gz
install -m 0755 -o root -g root -t /usr/local/bin lnd-linux-amd64-v0.16.2-beta/*
lnd --version
```

## Install and Configure Tor

```
apt install tor
systemctl enable tor
```

Modify /etc/tor/torrc, ensuring the following:

```
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
CookieAuthFileGroupReadable 1
```

Restart Tor:
```
systemctl restart tor
```

Create a limited service user that lnd will run as, and add to the debian-tor group so lnd can use Tor.
```
adduser --disabled-password --gecos "" lnd
usermod -a -G debian-tor lnd
```

Create the .lnd dir
```
su - lnd
cd
mkdir .lnd
chmod 750 .lnd
```

## Configure LND

(for playing around, we use openssl's random number generator, since we're only dealing with testnet coins)
Create a wallet password file:
```
openssl rand -base64 32 | tr -d '\n' > .lnd/password.txt
chmod 600 .lnd/password.txt
```

Create an .lnd/lnd.conf file, and ensure the core lines are set.
```
cd .lnd
wget https://raw.githubusercontent.com/lightningnetwork/lnd/master/sample-lnd.conf
cp sample-lnd.conf lnd.conf
chmod 600 lnd.conf
```

On the bitcoin node, create a new rpc user and store it into bitcoin.conf:
```
bitcoin/share/rpcauth/rpcauth.py btcmempooluser <RPC PASSWORD>
```

.lnd/lnd.conf updates:
```
;tlsextraip=0.0.0.0
;tlsextradomain=0.0.0.0
listen=127.0.0.1:9735
rpclisten=127.0.0.1:10009
restlisten=<IP WITHIN SUBNET WITH BITCOIND>:8080
wallet-unlock-password-file=/home/lnd/.lnd/password.txt
; wallet-unlock-allow-create=true should be set to false right after creation of the wallet
wallet-unlock-allow-create=true
alias=Foo
[Bitcoin]
bitcoin.active=true
;bitcoin.mainnet=true
bitcoin.testnet=true
;bitcoin.simnet=true
;bitcoin.node=btcd
bitcoin.node=bitcoind
[Bitcoind]
bitcoind.rpchost=<BITCOIND ADDRESS WITHIN SUBNET>
bitcoind.rpcuser=<rpcauth username in bitcoind.conf, e.g. btclnd2>
bitcoind.rpcpass=<associated password for the rpcauth entry in bitcoind.conf>
bitcoind.zmqpubrawblock=tcp://<BITCOIND ADDRESS WITHIN SUBNET>:28342
bitcoind.zmqpubrawtx=tcp://<BITCOIND ADDRESS WITHIN SUBNET>:28343
[tor]
; Tor settings commented out on first start (after wallet creation) to allow clearnet bootstrapping (TODO:  BOOTSTRAP OVER TOR INSTEAD?!), then uncommented to prevent clearnet
tor.active=true
tor.socks=9050
tor.streamisolation=true
tor.control=9051
tor.v3=true
```

## Setting up Static Channel Backup (SCB) Regular Archiving
Important for static channel backups to be saved locally as well as archived to another physical machine.

TODO: Finish this


## Initial run and wallet creation

```
su - lnd
lnd
```

In second terminal session (in tmux, ssh won't work for user lnd):
```
su - lnd
lncli create
```

Enter password matching password.txt.
Select 'n' when asked if you have an existing seed.
Press enter if asked about additional seed passphrase.
Write down the 24 word mnemonic.

## Configure lnd to start on boot, and run lnd

```exit``` terminal session running lnd.

As root, create the following systemd script in ```/etc/systemd/system/lnd.service```:

```
# A sample systemd service file for lnd running with a bitcoind service.

[Unit]
Description=Lightning Network Daemon

# Make sure lnd starts after bitcoind is ready
Requires=tor.service
After=tor.service

[Service]
ExecStart=/usr/local/bin/lnd
ExecStop=/usr/local/bin/lncli -n testnet stop

# Replace these with the user:group that will run lnd
User=lnd
Group=lnd

# Try restarting lnd if it stops due to a failure
Restart=on-failure
RestartSec=60

# Type=notify is required for lnd to notify systemd when it is ready
Type=notify

# An extended timeout period is needed to allow for database compaction
# and other time intensive operations during startup. We also extend the
# stop timeout to ensure graceful shutdowns of lnd.
TimeoutStartSec=1200
TimeoutStopSec=3600

# Hardening Measures

# Mount /usr, /boot/ and /etc read-only for the process.
ProtectSystem=full

# Disallow the process and all of its children to gain
# new privileges through execve().
NoNewPrivileges=true

# Use a new /dev namespace only populated with API pseudo devices
# such as /dev/null, /dev/zero and /dev/random.
PrivateDevices=true

# Deny the creation of writable and executable memory mappings.
MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
```

Enable:
```
systemctl enable lnd
systemctl start lnd
systemctl status lnd
```

to check deamon logging:
```
journalctl -fu lnd
```

## Fund the Node

```
lncli newaddress p2wkh
```

Send to the address.

```
lncli walletbalance
```

## Connect to a Node and Open a Channel

https://docs.lightning.engineering/the-lightning-network/liquidity/manage-liquidity

```
openchannel [command options] node-key local-amt push-amt
<node-key> = pubkey of other node, e.g. 03864ef025fde8fb587d989186ce6a4a186895ee44a926bfc370e2c366597a3f8f
<local-amt> = Amount, in sats, to define both your share of the channel as well as its full capacity.
<push-amt> = Amount, in sats, to send to the channel peer when creating the channel
```

The ```--private option``` is for creating an unanounced channel.
The ```--close_address``` option is used for sending bitcoin to another wallet address (e.g. cold) on cooperative close.

```
lncli connect <pubkey>@<host>:<port>
lncli openchannel --sat_per_vbyte 1 <pubkey> <local-amt> <push-amt>
e.g. lncli openchannel --sat_per_vbyte 1 03864ef025fde8fb587d989186ce6a4a186895ee44a926bfc370e2c366597a3f8f 100000 0
```

## Sending Payment

Keysend payment only requires knowing the recipient's pubkey
```
lncli sendpayment --dest <pubkey of receiving entity> --amt <in sats> --keysend
```

## Adding watchtowers
TODO: Finish this

## Useful Commands
```
lncli getinfo
lncli listpeers
lncli pendingchannels
lncli listchannels
lncli walletbalance
lncli channelbalance
lncli decodepayreq <invoice, lnbc...>
lncli payinvoice <invoice>
lncli listpayments
lncli addinvoice <amount in sats> (Our side creating an invoice)
lncli listinvoices
lncli closechannel --sat_per_vbyte <feerate> <funding txid> <output_index> (obtain FUNDING_TXID and OUTPUT_INDEX from lncli listchannels)
```
