import logging

import tomli
import requests
import json
import time
import threading

from computing_provider.api.node_service import generate_node_id

# Set the interval for sending the heartbeat message (in seconds)
interval = 5

def config():
    with open("config/config.toml", mode="rb") as fp:
        sys_config = tomli.load(fp)
    return sys_config


def heartbeat():
    node_id, peer_id = generate_node_id()
    sys_config = config()
    api_url = sys_config.get("main")["api_url"]
    lagrange_key = sys_config.get("main")["lagrange_key"]

    url = api_url + "/cp/heartbeat"
    headers = {
        'Authorization': 'Bearer ' + lagrange_key,
        'Content-Type': 'application/json',
    }
    body = {
        "node_id": node_id,
        "status": "Active"
    }
    while True:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        if response.ok:
            logging.info(f"Heartbeat request sent successfully.%s" % response.json())
        else:
            logging.warning(f"Failed to send heartbeat request.%s" % response.json())
        time.sleep(interval)


def cp_register():
    node_id, peer_id = generate_node_id()
    sys_config = config()
    api_url = sys_config.get("main")["api_url"]
    name = sys_config.get("main")["computing_provider_name"]
    multi_address = sys_config.get("main")["multi_address"]
    lagrange_key = sys_config.get("main")["lagrange_key"]

    logging.info("Node started: %s peer id: %s" % (node_id, peer_id))
    url = api_url + "/cp"
    headers = {
        'Authorization': 'Bearer ' + lagrange_key,
        'Content-Type': 'application/json',
    }
    body = {
        "name": name,
        "node_id": node_id,
        "multi_address": multi_address,
        "autobid": 1,
        "score": 0
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))

    if not response.ok:
        logging.warning(f"Failed to update cp info.%s" % response.json())

    heartbeat_thread = threading.Thread(target=heartbeat)
    heartbeat_thread.start()
