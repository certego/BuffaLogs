# Adding SSL Support for HTTPS Connections

SSL (Secure Sockets Layer) is the foundation of the HTTPS (Hypertext Transfer Protocol Secure) protocol on the web. Communication over SSL involves the exchange of an SSL certificate between the web server and the browser to establish a secure connection.

When a user visits an HTTPS website, the web server provides an SSL certificate containing information about the website’s identity. The browser verifies this certificate to ensure it is valid and issued by a trusted authority. If verification is successful, the browser and server establish an encrypted connection using SSL/TLS (Transport Layer Security), ensuring that data remains protected from eavesdropping and tampering.

To enable HTTPS on a website, the server requires:

1. An SSL Certificate – A file that proves the website's authenticity.


2. A Private Key – A secret key stored on the server, used to encrypt and decrypt data securely.



By default, Buffalogs only supports http on localhost. In this guide, we will use mkcert, a simple tool for creating trusted SSL certificates locally. This will allow localhost to accept secure https connections instead of http.


---

Installing mkcert

mkcert supports Windows, macOS, and Linux. You can find installation instructions for your platform in the mkcert GitHub repository. Follow the instructions for your system before proceeding.

Once mkcert is installed, you can move on to the next step.


---

Generating an SSL Certificate

If you are running mkcert for the first time, you need to create a local Certificate Authority (CA).
A Certificate Authority (CA) is a trusted organization that issues and verifies SSL/TLS certificates, ensuring secure HTTPS connections. Without Certificate Authorities, HTTPS security would be unreliable.

mkcert creates a local Certificate Authority and uses it to sign SSL certificates. To create the CA, run:

mkcert -install

This should output something like:

```
Created a new local CA at <directory> 💥
The local CA is now installed in the system trust store! ⚡️
The local CA is now installed in the Firefox trust store (requires browser restart)! 🦊
```

After creating the local CA, generate an SSL certificate for localhost by running:

```bash
mkcert -key-file key.pem -cert-file cert.pem localhost
```

This will create two files:

- cert.pem – The public certificate file used by the server, which the browser verifies before establishing a connection.

- key.pem – The private key used for decrypting messages from the client. This must be kept secret.



---

Configuring Nginx

Next, move the generated certificate files (key.pem and cert.pem) to the designated folder.

Step 1: Organizing the Certificate Files

Create a folder named certs inside project_root/config/nginx/. Your folder structure should look like this:
```
config/
├── buffalogs
│   ├── alerting.json
│   └── buffalogs.env
├── elasticsearch
│   ├── example_template.json
│   └── load_templates.sh
├── nginx
│   ├── certs
│   │   ├── cert.pem
│   │   └── key.pem
│   └── conf.d
│       ├── base.conf
│       ├── site.conf
│       └── upstream.conf
└── rabbitmq
    ├── advanced.config
    ├── definitions.json
    ├── enabled_plugins
    └── rabbitmq.conf
```
Step 2: Updating Nginx Configuration

Edit site.conf located in config/nginx/conf.d/. Change the existing configuration:

Before:
    
```
server{                                                                                                                                                       
    autoindex off;
    listen 80;
    server_name localhost;
    client_max_body_size 30M;

    location /static/ {
        alias /var/www/static/;
    }

    location / {
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
    }
}
```
    
After:

```
server{                                                                                                                                                                                                           
    autoindex off;
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 30M;

    location /static/ {
        alias /var/www/static/;
    }

    location / {
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
    }
}

# Redirect HTTP traffic to HTTPS
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}
```
    
This configuration:

Enables SSL on port 443, using cert.pem and key.pem.

Enforces HTTPS-only connections by redirecting HTTP requests from port 80 to 443.



---

Updating Docker Compose Configuration

To ensure that Nginx can access the certificates in the container, update the docker-compose.yaml file.

Before:

 ```yaml
buffalogs_nginx:
    container_name: buffalogs_nginx
    image: nginx:mainline-alpine
    hostname: nginx
    depends_on:
        - buffalogs
    volumes:
        - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
        #- ./config/nginx/certs:/etc/nginx/certs:ro
        - buffalogs_django_static:/var/www:ro
        - buffalogs_nginx_sockets:/var/run/nginx-sockets
        - buffalogs_nginx_logs:/var/log/nginx:rw
    ports:
        - "80:80"
```
    
After:

 ```yaml
buffalogs_nginx:
    container_name: buffalogs_nginx
    image: nginx:mainline-alpine
    hostname: nginx
    depends_on:
        - buffalogs
    volumes:
        - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
        - ./config/nginx/certs:/etc/nginx/certs:ro
        - buffalogs_django_static:/var/www:ro
        - buffalogs_nginx_sockets:/var/run/nginx-sockets
        - buffalogs_nginx_logs:/var/log/nginx:rw
    ports:
        - "80:80"
        - "443:443"
```
    
Changes made:

Uncommented ./config/nginx/certs:/etc/nginx/certs:ro, allowing the certs folder to be available inside the container.

Exposed port 443 to allow HTTPS traffic.



---

Restarting the Containers

If the Buffalogs containers are running, stop them first:

 ```bash
docker-compose down --remove-orphans
```

⚠️ This command will remove all running containers, so ensure no other important containers are affected. Alternatively, you can stop only the Buffalogs containers:

 ```bash
docker container rm <container_name>
```
    
After stopping the containers, rebuild and restart them:

```bash
docker-compose -f docker-compose.yaml -f docker-compose.elastic.yaml up -d
```
 
Finally, navigate to http://localhost:80. If everything is configured correctly, it should automatically redirect to https://localhost.


---

Conclusion

By following this guide, you have successfully enabled SSL on localhost for Buffalogs using mkcert and configured Nginx to serve HTTPS traffic. Now, all connections will be encrypted, ensuring secure communication between the server and the browser.


