# **Adding SSL Support for HTTPS connections**

SSL (**Secure Sockets Layer**) is the base of HTTPS (**Hypertext Transfer Protocol Secure**) protocol over the web. Communication over SSL involves the exchange of an **SSL certificate** with the browser to establish a **secure connection**.  

When a user visits an **HTTPS** website, the web server provides an **SSL certificate**, which contains information about the website’s identity. The browser verifies this certificate to ensure it is valid and issued by a trusted authority. If the verification is successful, the browser and server establish an **encrypted connection** using **SSL/TLS (Transport Layer Security)**, ensuring that data is protected from eavesdropping and tampering.  

To enable **HTTPS** on a website, the server needs:  
1. **An SSL Certificate** – A file that proves the website's authenticity.  
2. **A Private Key** – A secret key stored on the server, used to encrypt and decrypt data securely.  


Buffalogs by default only supports `http` on `localhost`, in this guide we make use of [mkcert](https://github.com/FiloSottile/mkcert) 
a simple tool for creating trusted SSL certificates locally to allow connections on `localhost` over  `https` rather than `http`. 


### **Installing mkcert**  

Currently, **mkcert** supports windows, mac-os and linux platforms and provide installation guide on their [github repo](https://github.com/FiloSottile/mkcert). You can briefly head over and follow the installation instruction for your platform before following on with the rest of the guide.

If you did follow the guide it means you have `mkcert` installed and you are ready to move to the next step.

### **Generating an SSL Certificate**  

If you are running `mkcert` for the first time, you will have to create a local **Certificate Authority**. 
A **Certificate Authority (CA)** is a trusted organization that issues and verifies SSL/TLS certificates. These certificates 
are used to establish secure HTTPS connections basically, without Certificate Authorities, the security of HTTPS would be unreliable. 

`mkcert` creates a local **Certificate Authority** and create signed SSL certificate using the local **Certificate Authority**. To create the **CA** simply enter the command: 

```bash
mkcert -install
```

This should give something similar to this

```
Created a new local CA at <directory> 💥
The local CA is now installed in the system trust store! ⚡️
The local CA is now installed in the Firefox trust store (requires browser restart)! 🦊
```

After creating the local **CA**, we can now generate an actual SSL certificate that will be verified by the CA. To create a certificate for `localhost`  run


```bash
mkcert -key-file key.pem -cert-file cert.pem localhost
```

This creates two files:
- `key.pem`
- `cert.pem`

`cert.pem` is the public certificate file used by the server which the browser verifies before making connection
`key.pem` contains the private key used for decrypting messages from the client. **This must be kept secret.**

### Configuring Nginx

To begin the configuration for nginx, we have to first move the two files generated to the designated folder

Create the folder `certs` in the `project_root/config/nginx/`. You should endup with a similar tree structure

```config/
├── buffalogs
│   ├── alerting.json
│   └── buffalogs.env
├── elasticsearch
│   ├── example_template.json
│   └── load_templates.sh
├── nginx
│   ├── certs
│   │   ├── cert.pem
│   │   └── key.pem
│   └── conf.d
│       ├── base.conf
│       ├── site.conf
│       └── upstream.conf
└── rabbitmq
    ├── advanced.config
    ├── definitions.json
    ├── enabled_plugins
    └── rabbitmq.conf
```

Once we have accomplished this, we will edit `site.conf` under `config/nginx/conf.d`. Change the code from

```
server{                                                                                                                                                       
                                                                                                                                                              
    # https://nginx.org/en/docs/http/ngx_http_autoindex_module.html                                                                                           
    autoindex off;                                                                                                                                            
                                                                                                                                                              
    listen 80;                                                                                                                                                
                                                                                                                                                              
    server_name localhost;                                                                                                                                    
                                                                                                                                                              
    # max upload size                                                                                                                                         
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

to

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
                                                                                                                                                                                                                  
    # max upload size                                                                                                                                                                                             
    client_max_body_size 30M;                                                                                                                                                                                     
                                                                                                                                                                                                                  
    location /static/ {                                                                                                                                                                                           
        alias /var/www/static/;                                                                                                                                                                                   
    }                                                                                                                                                                                                             
                                                                                                                                                                                                                  
    location / {                                                                                                                                                                                                  
        uwsgi_pass django;                                                                                                                                                                                        
        include /etc/nginx/uwsgi_params;                                                                                                                                                                          
    }                                                                                                                                                                                                             
                                                                                                                                                                                                                  
}                                                                                                                                                                                                                 
                                                                                                                                                                                                                  
# If somebody tries to connect to the server using http, he/she will be redirected in order to use https                                                                                                          
server {                                                                                                                                                                                                          
        listen 80;                                                                                                                                                                                                
        server_name localhost;                                                                                                                                                                                    
        return 301 https://$host$request_uri;                                                                                                                                                                     
} 
```

We have added a server block that listens on port `443` with `ssl` enabled. This server uses our `cert.pem` and `key.pem` files to perform https communications. 
We also added another server block that redirects request to `http:localhost:80` to `https:localhost`. This way we ensure that all the request are performed only over https.

For the final part, we will edit the docker compose file, specifically, the `buffalogs_nginx` container. 
Open `docker-compose.yaml` in the root folder, and scroll to the code 

```
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

and edit it to this

```
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

By uncommenting `./config/nginx/certs:/etc/nginx/certs:ro`, we are telling docker to move our `certs` folder containing the `key.pem` and `cert.pem` to 
`etc/nginx/certs` of the docker image. We also exposed the ssl port `443:443`. At this point, if you have the docker images running, you will have to 
stop them using

```bash
docker-compose down --remove-orphans
```

This will delete all the docker containers running, so you might want to take care running this if you have other container that you wish to keep running. Alternatively, you can use 

```bash
docker container rm <container_name>
```
for each of the buffalogs container. After removing the previous containers, you will have to build up the edited images running

```
docker-compose -f docker-compose.yaml -f docker-compose.elastic.yaml up -d
```
from the project root folder or the folder container the docker files. Navigating to [http://localhost:80](http://localhost:80) should redirect you to [https://localhost](https://localhost) if the configuration and build up were successful.
