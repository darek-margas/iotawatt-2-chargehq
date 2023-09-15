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
my_parser.add_argument( "--ip", metavar="IP address", type=str, help="IP Address of IoTaWatt", required=True )
my_parser.add_argument( "--grid", metavar="Net grid import", type=str, help="Net import from Grid (kW)", required=True )
my_parser.add_argument( "--production", metavar="PV production", type=str, help="PV production (kW)", required=True)
my_parser.add_argument( "--key", metavar="API key", type=str, help="ChargeHQ API key", required=True)

args = my_parser.parse_args()

# Charge HQ
chq_url = 'https://api.chargehq.net/api/public/push-solar-data'

try:
    # Getting data
    g = requests.get( "http://{}/query".format(args.ip), params = "select=[{}.watts,{}.watts]&begin=s-1m&end=s&group=all&header=no".format(args.grid, args.production), timeout=15)

    #Assembling json
    data = {}
    data['apiKey'] = args.key
    if g.status_code == 200:
       logging.info("Iotawatt collection successful")
       data['siteMeters'] = {}
       data['siteMeters']['production_kw'] = round( g.json()[0][1] / 1000, 3)
       data['siteMeters']['net_import_kw'] = round( g.json()[0][0] / 1000, 3)
       data['siteMeters']['consumption_kw'] = round( sum(g.json()[0])/1000,3)
    else:
       data['error'] = "Collection error: " +g.reason

    # Posting to CHQ
    payload = json.dumps(data)
    header = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    p = requests.post( chq_url, data=payload, headers=header)
    if p.status_code != 200:
       logging.warning("ChargeHQ API error: " + p.reason)
       error = "ChargeHQ API error: " + p.reason
    else:
       error = None
    #print(payload, p.text)
    logging.info(payload, p.text)
    
    return (payload, p.text, error)

except requests.exceptions.Timeout:
    logging.error("Timeout error: Request timed out")
    return (None, None, "Timeout error: Request timed out")
except requests.exceptions.ConnectionError as e:
    logging.error("Connection error: {}".format(str(e)))
    return (None, None, "Connection error: {}".format(str(e)))
except requests.exceptions.RequestException as e:
    logging.error("Error: " + str(e))
    return (None, None, "Error: " + str(e)))
