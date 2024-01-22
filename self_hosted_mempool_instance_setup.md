# Basic/Simplified Self Hosted Mempool.space Instance
The following is minimal/basic setup for a self-hosted Mempool web application instance (some basic sysadmin experience required).
It's not meant to be for high volume production environments (check out https://github.com/mempool/mempool/blob/master/production for more serious installations)

In this example, our local machine has the private IP address 10.0.0.30/24.

## Install Docker (e.g. Engine, containerd, Compose)
We'll be using Mempool's docker images, so we'll need to install Docker (if not already installed on the system).
Follow steps at https://docs.docker.com/engine/install/ubuntu/, including "Post-installation steps for Linux."

We create a new user that will run the containers, and add it to the `docker` group:
```
adduser mempool
usermod -aG docker mempool
```

## Install bitcoind and fulcrum
If not already installed, install bitcoind (either compile from source https://github.com/bitcoin/bitcoin/tree/master/doc or from https://bitcoincore.org/en/download/).  Detailed instructions can be found elsewhere, but below are a few bitcoin.conf parameters and a systemd script to start bitcoind on boot.  In this example, we're configuring bitcoind to run on a custom Signet.

We'll be running mempool in docker and fulcrum outside of docker, so we'll need to allow hosts from a docker subnet (established for the mempool containers) and fulcrum to reach RPC on bitcoind.

We'll also need to create two rpcauth strings for mempool and fulcrum, by running bitcoin/share/rpcauth from Bitcoin Core (https://github.com/bitcoin/bitcoin/tree/v26.0/share/rpcauth).  We'll need indexing turned on for bitcoind (reindex if needed for an existing bitcoind installation).  In this example, we add a signet partner node explicitly.

Example /home/bitcoin/.bitcoin/bitcoin.conf:
```
v2transport=1
rpcallowip=127.0.0.1
rpcallowip=10.0.0.30
rpcallowip=172.18.0.0/24

# for fulcrum
rpcauth=fulcrumuser1:<rpcauthoutput>
#reindex=1
txindex=1

# for mempool
rpcauth=mempooluser1:<rpcauthoutput>

signet=1
[signet]
signetchallenge=<THE SIGNET CHALLENGE>
addnode=<ANOTHER SIGNET NODE>:<SIGNET NODE PORT>
rpcbind=127.0.0.1
rpcbind=10.0.0.30
```

Example /etc/systemd/system/btcsig.service (install/start with `systemctl daemon-reload`, `systemctl enable btcsig`, `systemctl start btcsig`):
```
[Unit]
Description=Bitcoin daemon signet

After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/bitcoind -signet -daemonwait -conf=/home/bitcoin/.bitcoin/bitcoin.conf -datadir=/home/bitcoin/.bitcoin

Type=forking
Restart=on-failure
TimeoutStartSec=infinity
TimeoutStopSec=600

User=bitcoin
Group=bitcoin

PrivateTmp=true
ProtectSystem=full

NoNewPrivileges=true

# Use a new /dev namespace only populated with API pseudo devices
# such as /dev/null, /dev/zero and /dev/random.
PrivateDevices=true

MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
```

Status of bitcoind can be viewed through `systemctl status btcsig` and `/home/bitcoin/.bitcoin/signet/debug.log`.


If not already installed, install fulcrum to enhance the Mempool instance's capabilities (e.g. searching by address, etc.):
```
adduser fulcrum
su fulcrum
cd
mkdir fulcrumStorage
```

Obtain fulcrum (https://github.com/cculianu/Fulcrum/releases):
```
wget https://github.com/cculianu/Fulcrum/releases/download/v1.9.8/Fulcrum-1.9.8-x86_64-linux.tar.gz
mkdir fulcrum
tar xvf Fulcrum-1.9.1-x86_64-linux.tar.gz
mv Fulcrum-1.9.1-x86_64-linux/* fulcrum
```
If you're planning on having fulcrum be reached outside of the local machine, it is recommended to create/configure an SSL/TLS key and certificate for it.  In this example, fulcrum is being used/reached locally.

Create the fulcrum config:
```
cd fulcrum
cp fulcrum-example-config.conf fulcrum.conf
```

Modify the fulcrum.conf to point to bitcoind, and use the correct RPC credentials.
```
datadir = /home/fulcrum/fulcrumStorage
bitcoind = 127.0.0.1:38332
rpcuser = fulcrumuser1
rpcpassword = <PASSWORD USED WHEN RUNNING rpcauth.py>
tcp = 10.0.0.30:50001
# if using ssl/tls
#ssl = 0.0.0.0:50002 
#cert = /home/fulcrum/fulcrum/cert.pem
#key = /home/fulcrum/fulcrum/key.pem
peering = false
```

Fulcrum will listen on 10.0.0.30, port 50001, but is not allowed from addresses other than docker's, enforced by iptables.

Example /etc/systemd/system/fulcrum.service (install/start with `systemctl daemon-reload`, `systemctl enable fulcrum`, `systemctl start fulcrum`):
```
[Unit]
Description=Fulcrum
After=network.target

[Service]
ExecStart=/home/fulcrum/fulcrum/Fulcrum /home/fulcrum/fulcrum/fulcrum.conf
User=fulcrum
LimitNOFILE=8192
TimeoutStopSec=30min

[Install]
WantedBy=multi-user.target
```

Status of fulcrum can be viewed through `journalctl -fu fulcrum`
 


## Obtain the Mempool source
```
su mempool
cd
git clone https://github.com/mempool/mempool.git
```

Checkout a specific tag version as desired.


## Configure and run the Mempool instance

Our Mempool frontend will run on port 2080 on the local machine (8080 at the container).

Update `mempool/docker/docker-compose.yml`:

```
services:
  web:
    environment:
      FRONTEND_HTTP_PORT: "8080"
      BACKEND_MAINNET_HTTP_HOST: "api"
    image: mempool/frontend:latest
    user: "1000:1000"
    restart: always
    stop_grace_period: 1m
    command: "./wait-for db:3306 --timeout=720 -- nginx -g 'daemon off;'"
    ports:
      - 2080:8080
  api:
    environment:
      MEMPOOL_NETWORK: "signet"
      MEMPOOL_BACKEND: "electrum"
      ELECTRUM_HOST: "10.0.0.30"
      ELECTRUM_PORT: "50001"
      ELECTRUM_TLS_ENABLED: "false"
      CORE_RPC_HOST: "10.0.0.30"
      CORE_RPC_PORT: "38332"
      CORE_RPC_USERNAME: "mempooluser1"
      CORE_RPC_PASSWORD: "<PASSWORD USED WHEN RUNNING rpcauth.py>"
      CORE_RPC_TIMEOUT: "60000"
      DATABASE_ENABLED: "true"
      DATABASE_HOST: "db"
      DATABASE_DATABASE: "mempool"
      DATABASE_USERNAME: "mempool"
      DATABASE_PASSWORD: "<CHOSEN DB USER PASSWORD>"
      STATISTICS_ENABLED: "true"
    image: mempool/backend:latest
    user: "1000:1000"
    restart: always
    stop_grace_period: 1m
    command: "./wait-for-it.sh db:3306 --timeout=720 --strict -- ./start.sh"
    volumes:
      - ./data:/backend/cache
  db:
    environment:
      MYSQL_DATABASE: "mempool"
      MYSQL_USER: "mempool"
      MYSQL_PASSWORD: "<CHOSEN DB USER PASSWORD>"
      MYSQL_ROOT_PASSWORD: "<CHOSEN DB ROOT PASSWORD>"
    image: mariadb:10.5.21
    user: "1000:1000"
    restart: always
    stop_grace_period: 1m
    volumes:
      - ./mysql/data:/var/lib/mysql

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/24
```

Adjust the permissions of mempool/docker/data and mempool/docker/mysql directories to ensure the containers can write to them.
```
sudo chown -R 1000:1000 data mysql
```

## Running Mempool

```
cd mempool/docker
docker compose up -d   # -d = detached
```

Logging can be viewed with:
`docker logs <container ID>`


## Reachability
As a basic test, access your Mempool instance frontend at host:2080 (e.g. http://10.0.0.30:2080 in this case).
If having trouble try via ssh port forwarding first (e.g. `ssh -L2080:127.0.0.1:2080 user@host`).
Check logs (see steps above) for additional troubleshooting.

### Firewall rules
This would differ based on the environment.
If operating behind a firewall or within a cloud provider, you may have to add a security group/list rule to allow 2080.
Specifics of iptables configuration can be found elsewhere (e.g. https://www.digitalocean.com/community/tutorials/iptables-essentials-common-firewall-rules-and-commands)

For example (iptables):
```
-A INPUT -p tcp -m tcp --dport 2080 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A INPUT -p tcp -m tcp --sport 2080 -m conntrack --ctstate ESTABLISHED -j ACCEPT
```

### Proxying and TLS/SSL for the Frontend
You may want to publicly host the Mempool frontend.
For non-critical public environments, this may be done with a straightforward SSL/TLS cert installation (e.g. letsencrypt) and with a reverse proxy (e.g. using nginx).

Setting up an SSL/TLS cert with letsencrypt is described in https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04.

Below is a quick nginx proxying example.  This assumes DNS A records are properly set up.

```
server {

        root /var/www/<YOUR DOMAIN>/html;
        index index.html index.htm index.nginx-debian.html;

        server_name <YOUR DOMAIN>;

        location / {
                #try_files $uri $uri/ = 404;
                proxy_pass http://<YOUR DOMAIN>:2080;
                proxy_redirect http://<YOUR DOMAIN>:2080/ $scheme://$host:443/;
        }

        location /api/v1/ws {
                proxy_pass http://<YOUR DOMAIN>:2080;
                proxy_redirect http://<YOUR DOMAIN>:2080/ $scheme://$host:443/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
        }

        location /ws {
                proxy_pass http://<YOUR DOMAIN>:2080;
                proxy_redirect http://<YOUR DOMAIN>:2080/ $scheme://$host:443/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
        }
                


    listen [::]:443 ssl; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/<YOUR DOMAIN>/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/<YOUR DOMAIN>/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = <YOUR DOMAIN>) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


        listen 80;
        listen [::]:80;

        server_name <YOUR DOMAIN>;
    return 404; # managed by Certbot


}
```
