#   BuffaLogs

BuffaLogs is an Open Source Django Project whose main purpose is to detect impossible travel logins.

In details, it sends several types of alerts:
1.  **Impossible Travel**

    It occurs when a user logs into the system from a significant distance within a range of time that cannot be covered by conventional means of transport.

2.  **Login from new device**

    This alert is sent if the user utilizes a new appliance.

3.  **Login from a new country**

    This alert is dispatched if the system is logged by a user from a country where they have never authenticated before.

*For futher details: [Wiki - About](https://github.com/certego/BuffaLogs/wiki/1.-About)*

##  Installation & Running
BuffaLogs employs the following tools which have to be installed on the machine:
- [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
- [Docker-compose](https://docs.docker.com/compose/install/)
- [Python](https://www.python.org/downloads/)

Then, you clone this repository on your local computer with:

```bash
git clone git@github.com:certego/BuffaLogs.git
```
Then load the elasticsearch templates running the *load_templates.sh* script from *buffalogs_module/config/elasticsearch*:
```bash
./load_templates.sh
```
Now, you are ready to start up the application by running:
```bash
sudo docker-compose up -d
```
Results are available at `localhost:80`

![buffalogs_dashboard_screenshot](https://user-images.githubusercontent.com/33703137/220879987-b6453e9d-0129-45c1-bc26-0542005e8730.png)

*For futher examples: [Wiki - Example](https://github.com/certego/BuffaLogs/wiki/2.-Example)*

##   Logs Structure

BuffaLogs is able to analyse logs coming from any source, provided that it complies with the Elastic Common Schema and with the given structure: 

    ```
    {
        "user": {
            "name": <user_name>
        },
        "event": {
            "outcome": <"success" OR "failure">
        },
        "geoip": {
            "latitude": <latitude>,
            "longitude": <longitude>,
            "country_name": <country_name>
        },
        "user_agent": {
            "original": <user_agent>
        }
    }
    ```
For a basic analysis to detect only impossible travel logins, the *user_agent* field is useless.

##  BuffaLogs Architecture
![Buffalogs_Architecture](https://user-images.githubusercontent.com/33703137/220896332-4fe08f32-1879-4150-bd5d-9df9dc21a7a7.jpg)

*For futher details: [Wiki - Architecture](https://github.com/certego/BuffaLogs/wiki/3.-Architecture)*

##  Uninstall

To uninstall and remove all files, delete all containers with:
```
sudo docker-compose down -v
```
Then you can safely delete this repository.

