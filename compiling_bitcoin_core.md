### Compiling Bitcoin Core (Debian, v23)

#### Install dependencies (as root)

    su root
    apt update && apt install git build-essential libtool autotools-dev automake pkg-config bsdmainutils python3 libssl-dev libevent-dev libboost-system-dev libboost-filesystem-dev libboost-chrono-dev libboost-test-dev libboost-thread-dev libminiupnpc-dev libzmq3-dev libprotobuf-dev protobuf-compiler git ccache libsqlite3-dev

#### Create and become user 'bitcoin'

    /sbin/adduser bitcoin
    su bitcoin

#### Clone bitcoin core repo

    git clone https://github.com/bitcoin/bitcoin.git
    cd bitcoin

#### Checkout and compile

    git checkout v23.0
    ./contrib/install_db4.sh `pwd`
    ./autogen.sh
    export BDB_PREFIX='/home/bitcoin/bitcoin/db4'
    ls $BDB_PREFIX # test env var
    ./configure BDB_LIBS="-L${BDB_PREFIX}/lib -ldb_cxx-4.8" BDB_CFLAGS="-I${BDB_PREFIX}/include"
    make -j4 # or appropriate number of CPU cores

#### Post-compilation testing

    make check
    test/functional/test_runner.py

#### Install (as root)

    su root # or 'exit' to become root
    make install

#### Obtain bitcoin.conf (or use a pre-exising one)

    su bitcoin
    mkdir ~/.bitcoin
    cp share/examples/bitcoin.conf ~/.bitcoin/

Make adjustments to bitcoin.conf for installation needs (e.g., maxconnections, maxuploadtarget).

#### Start bitcoind 

On mainnet

    bitcoind -daemon

On testnet3

    bitcoind -testnet -daemon

Check logs for status details

    tail -f ~/.bitcoin/debug.log
    tail -f ~/.bitcoin/testnet3/debug.log
    
Stop bitcoind

    bitcoin-cli stop # for mainnet
    bitcoin-cli -testnet stop # for testnet3
    

