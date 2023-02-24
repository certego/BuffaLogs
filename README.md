# BuffaLogs
BuffaLogs is an Open Source Django Project whose main purpose is to detect impossible travel logins.

In details, it sends several types of alerts:
1.  **Impossible Travel**

    It occurs when a user logs into the system from a significant distance within a range of time that cannot be covered by conventional means of transport.

2.  **Login from new device**

    This alert is sent if the user utilizes a new appliance.

3.  **Login from a new country**

    This alert is dispatched if the system is logged by a user from a country where they have never authenticated before.

*For futher details: [Wiki - About](https://github.com/certego/BuffaLogs/wiki/1.-About)*

## BuffaLogs is participating in GSoC 2023 thanks to Honeynet project and IntelOwl!

| Honeynet | IntelOwl|
|------|-----|
|<a href="https://www.honeynet.org"> <img style="border: 0.2px solid black" width=115 height=150 src="https://user-images.githubusercontent.com/188858/221210754-7cdd600a-0a86-4718-863a-41091cf8b600.png" alt="Honeynet.org logo"> </a> | <a href="https://github.com/intelowlproject/IntelOwl/blob/master/README.md"><img src="https://user-images.githubusercontent.com/188858/221217292-25c1b3e4-cadb-491c-ac6a-d6d204d52e50.png" width=275 height=75 alt="Intel Owl"/> </a> |

### Google Summer Of Code

Since its birth, this project has been participating in the GSoC under the Honeynet Project!

* 2023: [Project available](https://github.com/intelowlproject/gsoc/tree/main/2023#4-buffalogs-login-monitoring-and-alerting-project)

Stay tuned for the upcoming GSoC! Join the [Honeynet Slack chat](https://gsoc-slack.honeynet.org/) for more info.

### GSoC Application process

#### 0. Get familiar with GSoC

First of all, and if you have not done that yet, read [the contributor guide](https://google.github.io/gsocguides/student/) which will allow you to understand all this process and how the program works overall. Refer to its left side menu to quick access sections that may interest you the most, although we recommend you to read everything.  
  
#### 1. Discuss the project idea with the mentor(s)

This is a required step and you can use the current issues as a start to propose your idea.

We are not limited to what is listed right now, if you want to propose a new idea, please discuss it with the mentors in Honeynet [slack](https://gsoc-slack.honeynet.org/) channel `#2023-buffalogs`. We're always open to new ideas and won't hesitate on choosing them if you demonstrate to be a good candidate!  
  
#### 2. Understand that

- You're committing to a project and we ask you to publicly publish your weekly progress on it in Github.
- We will ask you to give feedback on our mentorship and management continuously. Communication is key to the success of the project.
- You wholeheartedly agree with the [code of conduct](https://github.com/intelowlproject/IntelOwl/blob/master/CODE_OF_CONDUCT.md).
- You must tell us if there's any proposed idea that you don't think would fit the timeline or could be boring (yes, we're asking for feedback).
  
#### 3. Fill out the application form

We recommend you to follow [Google's guide to Writing a Proposal](https://google.github.io/gsocguides/student/writing-a-proposal).

Once you have a draft proposal please share it with us via gsoc [slack](https://gsoc-slack.honeynet.org/) channel `#2023-buffalogs`.

You can also ask for a review anytime to the community or mentor candidates before the contributor application deadline. It's much easier if you get feedback early than to wait for the last moment.

### Official communication channels
* [Slack chat](https://gsoc-slack.honeynet.org/)

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

