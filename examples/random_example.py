from datetime import datetime, timedelta
import random
from elasticsearch import Elasticsearch
import yaml

from elasticsearch.helpers import bulk


def main():
    fields = []
    es = Elasticsearch(["http://localhost:9200"])
    event_outcome = ["failure"] * 10 + ["success"] * 90
    event_category = ["threat"] * 2 + ["session"] * 2 + ["malware"] * 6 + ["authentication"] * 90
    now = datetime.utcnow() + timedelta(minutes=-30)
    with open("random_data.yaml", "r") as info:
        read_data = yaml.load(info, Loader=yaml.FullLoader)

    for i in range(0, 2000):
        tmp = {}
        ip = random.choice(read_data["ip"])
        str_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        head = str_time[:-4]
        tail = str_time[-1:]
        tmp["@timestamp"] = head + tail

        tmp["user"] = {"name": random.choice(read_data["user_name"])}
        tmp["event"] = {"outcome": random.choice(event_outcome)}
        tmp["event"] = {"category": random.choice(event_category)}
        tmp["source"] = {
            "ip": ip["address"],
            "geo": {
                "country_name": ip["country_name"],
            },
        }
        tmp["source"]["geo"]["location"] = {"lat": ip["latitude"], "lon": ip["longitude"]}
        tmp["user_agent"] = {"original": random.choice(read_data["user_agent"])}

        now = now + timedelta(seconds=1)

        fields.append(tmp)
    write_bulk(es, fields)


def write_bulk(es, msg_list):
    """Save a list of messages to sensor_stats index

    :param msg_list: a list of messages to save
    :type msg_list: list
    """
    bulk(es, _bulk_gendata("cloud-test_data", msg_list))


def _bulk_gendata(index, msg_list):
    for msg in msg_list:
        yield {"_op_type": "index", "_index": index, "_source": msg}


if __name__ == "__main__":
    main()
