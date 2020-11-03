import kubernetes
from kubernetes import client, config, watch
import os
import json
import traceback
import requests
import logging
import sys
import time

root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

logger = logging.getLogger("kubeslack")

logger.info("Loading config")

try:
    # try loading cluster config first
    kubernetes.config.load_incluster_config()
except:
    # if not, fall back to local kube config
    kubernetes.config.load_kube_config()


homedir = os.environ["HOME"]

with open(os.path.join(homedir, "channel")) as f:
    channel = f.read().strip()

with open(os.path.join(homedir, "token")) as f:
    token = f.read().strip()

logger.info("Starting")
status = {}

while True:
    try:
        c = client.CoreV1Api()

        for event in watch.Watch().stream(c.list_node, timeout_seconds=30):
            raw_object = event["raw_object"]
            # print(json.dumps(raw_object, indent=2))
            event_type = event['type']
            node_name = raw_object["metadata"]["name"]
            conditions = {}
            for condition in raw_object["status"]["conditions"]:
                conditions[condition["type"]] = condition["status"]
        
            old_conditions = status.get(node_name)
            if old_conditions is not None and old_conditions != conditions:
                logger.info(f"Name: {node_name} Event: {event_type} {json.dumps(conditions, indent=2)}")

                
                url = "https://slack.com/api/chat.postMessage"
                data = {
                    "channel": channel,
                    "text": f"Name: {node_name} Event: {event_type} {json.dumps(conditions, indent=2)}",
                    "username": "kubeslack"
                }
                logger.info(data)

                for i in range(0, 5):
                    rd = requests.post(url,
                                       headers={
                                           "Authorization": f"Bearer {token}",
                                           "Content-type": "application/json; charset=utf-8"
                                       },
                                       data=json.dumps(data),
                                       timeout=(10, 30))
                    if rd.status_code == 200:
                        logger.info(f"Posted message to slack: {node_name}")
                        break
                    else:
                        logger.error(f"Not able to post message to slack: {rd.status_code} {rd.text}")
                        
                    time.sleep(5)
                
            status[node_name] = conditions
            
    except KeyboardInterrupt:
        raise
    except:
        logger.exception("Failed for some reason")

    
    

