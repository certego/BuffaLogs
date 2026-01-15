## BuffaLogs Architecture
BuffaLogs is developed using different technologies:
*  Django - Python framework
*  Elasticsearch - Analytics engine
*  Kibana - GUI for Elasticsearch data
*  PostgreSQL - Object-relational database
*  Nginx - Web server
*  RabbitMQ - Message Broker
*  Celery - Task queue
*  Celery Beat - Periodic task scheduler

The general architecture is explained by the diagram below:
![Buffalogs_Architecture](https://user-images.githubusercontent.com/33703137/220964092-2188eff6-47e9-495d-9406-c436c2af61ef.jpg)

### Django
[Django](https://www.djangoproject.com/) is a high-level Python application development framework.

### Elasticsearch
[Elasticsearch](https://www.elastic.co/elasticsearch/) allows you to store, search, and analyze huge volumes of data quickly and in near real-time and give back answers in milliseconds.

### Kibana
[Kibana](https://www.elastic.co/kibana/) is a visual interface tool mainly used to analyze large volumes of log data massed in Elasticsearch.

### Nginx 
[Nginx](https://www.nginx.com) is an open-source web server, also used as a reverse proxy, HTTP cache, and load balancer.

### PostgreSQL
[PostgreSQL](https://www.postgresql.org/) is an open-source relational database. It supports both SQL (relational) and JSON (non-relational) querying. 

### RabbitMQ
[RabbitMQ](https://www.rabbitmq.com/) is a message-queueing software to which applications connect in order to transfer messages.
A message could have information about a process or task that should start on another application.
The queue-manager software stores the messages until a receiving application connects and takes a message off the queue, in order to process it.
Message queueing allows web servers to respond to requests quickly instead of being forced to perform resource-heavy procedures on the spot that may delay response time.

### Celery
[Celery](https://docs.celeryq.dev/en/stable/) is the consumer in a scenario of producer and consumer. It handles any task that is waiting in the message broker (RabbitMQ).

### Celery Beat
[Celery Beat](https://docs.celeryq.dev/en/stable/reference/celery.beat.html) is the scheduler, so it keeps track of when tasks should be executed by Celery.
Celery would consume the tasks instantly, instead with Celery Beat the consumption of tasks is periodic.

## Development Environment Setup

For a complete containerized **backend** development environment that includes all the components mentioned above, see [Development with DevContainers](development_with_devcontainers.md). This provides a pre-configured setup with all services running and ready for development. 