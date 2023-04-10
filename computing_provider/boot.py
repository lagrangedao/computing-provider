import logging

import tomli
import requests

from computing_provider.api.node_service import generate_node_id


def config():
    with open("config/config.toml", mode="rb") as fp:
        sys_config = tomli.load(fp)
    return sys_config


def cp_register():
    node_id, peer_id = generate_node_id()
    sys_config = config()
    api_url = sys_config.get("main")["api_url"]
    name = sys_config.get("main")["computing_provider_name"]
    multi_address = sys_config.get("main")["multi_address"]
    lagrange_key = sys_config.get("main")["lagrange_key"]

    logging.info("Node started: %s peer id: %s" % (node_id, peer_id))
    url = api_url + "/cp"
    headers_auth = {
        'Authorization': 'Bearer ' + lagrange_key,
    }
    body = {
        "name": name,
        "node_id": node_id,
        "multi_address": multi_address
    }
    response = requests.post(url, headers=headers_auth, data=body)

    if not response.ok:
        logging.warning(f"Failed to update cp info.%s" % response.json())
