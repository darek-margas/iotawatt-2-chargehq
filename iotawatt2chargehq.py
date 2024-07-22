#!/usr/bin/env python3
import sys, os
import locale
import json
import requests
import argparse
import logging
import time

__author__ = "Darek Margas"
__copyright__ = "Copyright 2023, Darek Margas"
__license__ = "MIT"

# Arguments
my_parser = argparse.ArgumentParser(description="Update ChargeHQ from IoTaWatt")
my_parser.add_argument("--ip", metavar="IP address", type=str, help="IP Address of IoTaWatt", required=True)
my_parser.add_argument("--grid", metavar="Net grid import", type=str, help="Net import from Grid (kW)", required=True)
my_parser.add_argument("--production", metavar="PV production", type=str, help="PV production (kW)", required=True)
my_parser.add_argument("--key", metavar="API key", type=str, help="ChargeHQ API key", required=True)
args = my_parser.parse_args()

# Charge HQ
chq_url = 'https://api.chargehq.net/api/public/push-solar-data'

# Getting data
data = {}
data['apiKey'] = args.key

try:
    g = requests.get(
        f"http://{args.ip}/query",
        params=f"select=[{args.grid}.watts,{args.production}.watts]&begin=s-1m&end=s&group=all&header=no",
        timeout=15
    )
    g.raise_for_status()  # Raises an HTTPError for bad responses

    logging.info("Iotawatt collection successful")
    data['siteMeters'] = {}
    data['siteMeters']['production_kw'] = round(g.json()[0][1] / 1000, 3)
    data['siteMeters']['net_import_kw'] = round(g.json()[0][0] / 1000, 3)
    data['siteMeters']['consumption_kw'] = round(sum(g.json()[0])/1000, 3)

except requests.exceptions.RequestException as e:
    # This catches all requests-related errors, including connection errors
    error_message = "Unable to read data: " + str(e)
    logging.error(error_message)
    data['error'] = error_message

# Posting to CHQ
payload = json.dumps(data)
header = {'Content-type': 'application/json', 'Accept': 'text/plain'}

try:
    p = requests.post(chq_url, data=payload, headers=header)
    p.raise_for_status()
    logging.info(f"Data sent to ChargeHQ: {payload}")
    logging.info(f"ChargeHQ response: {p.text}")
except requests.exceptions.RequestException as e:
    logging.error(f"Error sending data to ChargeHQ: {str(e)}")
