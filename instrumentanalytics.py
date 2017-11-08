# Copyright 2015 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import json
import argparse
import os
from dotenv import load_dotenv

#Simulated Instrument Analytics service credentials
if 'VCAP_SERVICES' in os.environ:
    vcap_servicesData = json.loads(os.environ['VCAP_SERVICES'])
    # Log the fact that we successfully found some service information.
    print("Got vcap_servicesData\n")
    # Look for the Simulated Instrument Analytics service instance
    access_token=vcap_servicesData['fss-instrument-analytics-service'][0]['credentials']['accessToken']
    uri=vcap_servicesData['fss-instrument-analytics-service'][0]['credentials']['uri']
    # Log the fact that we successfully found credentials
    print("Got IA credentials\n")
else:
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    uri=os.environ.get("IA_uri")
    access_token=os.environ.get("IA_access_token")
    

def Compute_InstrumentAnalytics(instrument_ids, analytics=None):
    """
    Retreives the Simulated Instrument Analytics service data, pass the instrument_id and scernario file
    """
    #print for logging purpose
    print ("Compute Instrument Analytics")

    if not analytics:
        analytics = ['THEO/Price','THEO/Value']

    payload = {"compute_request": {
            "instruments":instrument_ids,
            "analytics":analytics
        }}
    payload = json.dumps(payload) #service expects a string?

    #call the url
    BASEURL = uri + 'api/v1/instruments'
    headers = {
        'accept':'application/json',
        'Content-Type':'application/x-www-form-urlencoded',
        'X-IBM-Access-Token': access_token
        }
    get_data = requests.post(BASEURL, headers=headers, data=payload)
    print("Instrument Analytics status: " + str(get_data.status_code))

    #return json data
    data = get_data.json()
    return data
