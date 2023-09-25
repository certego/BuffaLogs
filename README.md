# BuffaLogs
BuffaLogs is an Open Source Django Project whose main purpose is to detect impossible travel logins.

In detail, it sends several types of alerts:
1.  **Impossible Travel**

    It occurs when a user logs into the system from a significant distance within a range of time that cannot be covered by conventional means of transport.

2.  **Login from new device**

    This alert is sent if the user utilizes a new appliance.

3.  **Login from a new country**

    This alert is dispatched if the system is logged by a user from a country where they have never authenticated before.

*For further details: [Wiki - About](https://github.com/certego/BuffaLogs/wiki/1.-About)*

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

Then, you can clone this repository on your local computer with:

```bash
git clone git@github.com:certego/BuffaLogs.git
```
Or download the application directly from the [Docker Hub](https://hub.docker.com/r/certego/buffalogs), with the `sudo docker pull certego/buffalogs:<release_tag>`.

After that, there are two ways of running BuffaLogs, depending on your system configurations:
* if you already have an elastic cluster:
    *  set the address of the host into the `CERTEGO_ELASTICSEARCH` variable in the `buffalogs.env` file
    *  launch ` docker-compose up -d` to run the containers
* if you have no hosts with Elasticsearch installed on it, you can run it directly with Buffalogs:
    * run `docker-compose -f docker-compose.yaml -f docker-compose.elastic.yaml up -d` in order to execute all the containers, included Elasticsearch and Kibana
    * Now elasticsearch and kibana are running on the same host with Buffalogs.

![Screenshot 2023-08-09 at 6 49 41 PM](https://github.com/certego/BuffaLogs/assets/33703137/07548d33-3878-4ff3-9cb7-4a6b865d233b)

*For further examples: [Wiki - Example](https://github.com/certego/BuffaLogs/wiki/3.-Example)*

##   Logs Structure

BuffaLogs is able to analyse logs coming from any source, provided that it complies with the Elastic Common Schema and with the given structure: 

    ```
    {
        "_index": "<elastic_index>",
        "_id": "<log_id>",
        "@timestamp": "<log_timestamp>",
        "user": {
            "name": "<user_name>"
        },
        "source": {
            "geo": {
                "country_name": "<country_origin_log>",
                "location": {
                    "lat": "<log_latitude>",
                    "lon": "<log_longitude>"
                }
            },
            "ip": "<log_source_ip>"
        },
        "user_agent": {
            "original": "<log_device_user_agent>"
        },
        "event": {
            "type": "start",
            "category": "authentication",
            "outcome": "success"
        }
    }

    ```
For a basic analysis to detect only impossible travel logins, the *user_agent* field is useless.

##  REST APIs

Five views were implemented using DRF - Django-Rest Framework, in order to provide the possible to query and produce the charts data.
In particular, the supplied APIs are:
| **API's name**| **API result**|
|---|---|
| *users_pie_chart_api* | It returns the association between the risk level and the number of users with that risk score |
| *alerts_line_chart_api* | It provides the number of alerts triggered in a particular timeframe |
| *world_map_chart_api* | It supplies the relation of countries and the number of alerts triggered from them |
| *alerts_api* | It offers the details about the alerts generated in the provided interval |
| *risk_score_api* | It provides the association between user and risk level for the users whose risk changed in the requested timeframe |

*For further details: [Wiki - REST APIs](https://github.com/certego/BuffaLogs/wiki/5.-REST-APIs)*

##  Uninstall

To uninstall and remove all files, delete all containers with:
```
sudo docker-compose down -v
```
Then you can safely delete this repository.

##  Contribution
BuffaLogs is an Open Source project and was developed in order to allow enrichments from people with any level of experience, but please read carefully the [Contribution guidelines](docs/CONTRIBUTING.md) before making any changes to the project.

## Release
1. If needed, update the requirements in the `requirements.txt` and also into the `setup.cfg` file
2. Add a new entry in `CHANGELOG.md` containing all the features, changes and bugfix developed
3. Modify the **version** in the `setup.cfg`
4. Commit a PR from the develop to the main branch with the version as a Title and the changes as a comment

## Licence
This project is protected by the Apache Licence 2.0.
