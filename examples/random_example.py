import random
from datetime import datetime, timedelta

import yaml
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

NUM_LOGS = 2000


def main():
    es = Elasticsearch(["http://localhost:59200"])
    common_data_cloud_index = generate_common_data()
    write_bulk(es, "cloud", common_data_cloud_index)
    common_data_weblog_index = generate_common_data()
    write_bulk(es, "weblog", common_data_weblog_index)
    common_data_fwproxy_index = generate_common_data()
    write_bulk(es, "fw-proxy", common_data_fwproxy_index)


def generate_common_data():
    fields = []
    event_outcome = ["failure"] * 10 + ["success"] * 90
    event_category = ["threat"] * 2 + ["session"] * 2 + ["malware"] * 6 + ["authentication"] * 90
    event_type = ["start"] * 80 + ["end"] * 20

    with open("random_data.yaml", "r") as info:
        read_data = yaml.load(info, Loader=yaml.FullLoader)

    for i in range(0, NUM_LOGS):
        tmp = {}
        ip = random.choice(read_data["ip"])
        now = datetime.utcnow()
        str_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        head = str_time[:-4]
        tail = str_time[-1:]
        tmp["@timestamp"] = head + tail

        tmp["user"] = {"name": random.choice(read_data["user_name"])}
        tmp["event"] = {"outcome": random.choice(event_outcome), "category": random.choice(event_category), "type": random.choice(event_type)}
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
    return fields


def write_bulk(es, index, msg_list):
    """Save a list of messages to sensor_stats index

    :param msg_list: a list of messages to save
    :type msg_list: list
    """
    now = datetime.utcnow()
    bulk(es, _bulk_gendata(f"{index}-test_data-{str(now.year)}-{str(now.month)}-{str(now.day)}", msg_list))


def _bulk_gendata(index, msg_list):
    for msg in msg_list:
        yield {"_op_type": "index", "_index": index, "_source": msg}


if __name__ == "__main__":
    main()
