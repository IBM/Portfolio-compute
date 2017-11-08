# Written by Rob Seidman on 10/03/2017
from flask import Flask, render_template, jsonify, json, url_for, request, redirect, Response, flash, abort, make_response, send_file
import requests
import StringIO
import io
import os
import csv
import datetime
import investmentportfolio
import instrumentanalytics

print ('Running portfolio.compute.py')
app = Flask(__name__)

# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))
host='0.0.0.0'

# I couldn't add the services to this instance of the app so VCAP is empty
# do this to workaround for now
if 'VCAP_SERVICES' in os.environ:
    if str(os.environ['VCAP_SERVICES']) == '{}':
        print ('Using a file to populate VCAP_SERVICES')
        with open('VCAP.json') as data_file:
            data = json.load(data_file)
        os.environ['VCAP_SERVICES'] = json.dumps(data)

#======================================RUN LOCAL======================================
# stuff for running locally
if 'RUN_LOCAL' in os.environ:
    print ('Running locally')
    port = int(os.getenv('SERVER_PORT', '5555'))
    host = os.getenv('SERVER_HOST', 'localhost')
    with open('VCAP.json') as data_file:
        data = json.load(data_file)
    os.environ['VCAP_SERVICES'] = json.dumps(data)

#======================================MAIN PAGES======================================
@app.route('/')
def run():
    """
    Load the site page
    """
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def portfolio_from_csv():
    """
    Loads a portfolio in Algo Risk Service (ARS) format into the Investment Portfolio service.
    """
    holdings = {
        'timestamp':'{:%Y-%m-%dT%H:%M:%S.%fZ}'.format(datetime.datetime.now()),
        'holdings':[]
    }
    data = json.loads(request.data)
    data = [row.split(',') for row in data]
    headers = data[0]
    #Loop through and segregate each portfolio by its identifier (there may be multiple in the file)
    #Column 1 (not 0) is the ID column. Column 5 is the PORTFOLIO column...
    portfolios = {}
    unique_id_col =  headers.index("UNIQUE ID")
    id_type_col =  headers.index("ID TYPE")
    name_col =  headers.index("NAME")
    pos_units_col =  headers.index("POSITION UNITS")
    portfolio_col =  headers.index("PORTFOLIO")
    price_col =  headers.index("PRICE")
    currency_col =  headers.index("CURRENCY")

    #for d in data...
    for d in data[1:]:
        hldg = {
            "name":d[name_col],
            "instrumentId":d[unique_id_col],
            "quantity":d[pos_units_col]
        }
        if len(headers)>5:
            for meta in headers[6:]:
                hldg[meta.replace('\r','')] = d[headers.index(meta)].replace('\r','')
        
        if d[portfolio_col] not in portfolios:       
            portfolios[d[portfolio_col]] = [hldg]
        else:
            portfolios[d[5]].append(hldg)
    
    #Send each portfolio and its holdings to the investment portfolio service
    for key, value in portfolios.iteritems():
        my_portfolio = {
            "timestamp": '{:%Y-%m-%dT%H:%M:%S.%fZ}'.format(datetime.datetime.now()) ,
            'closed':False,
            'data':{'type':'unit test portfolio'},
            'name':key
        }
        
        #create portfolio
        try:
            req  = investmentportfolio.Create_Portfolio(my_portfolio)
        except:
            print("Unable to create portfolio for " + str(key) + ".")
        
        try:
            for h in range(0,len(value),500):
                hldgs = value[h:h+500]
                req  = investmentportfolio.Create_Portfolio_Holdings(str(key),hldgs)
        except:
            print("Unable to create portfolio holdings for " + str(key) + ".")
    return req


#Returns list of 'unit test' portfolios
@app.route('/api/unit_test_portfolios',methods=['GET'])
def get_unit_test_portfolios():
    '''
    Returns the available user portfolio names in the Investment Portfolio service.
    Uses type='user_portfolio' to specify.
    '''
    portfolio_names = []
    res = investmentportfolio.Get_Portfolios_by_Selector('type','unit test portfolio')
    try:
        for portfolios in res['portfolios']:
            portfolio_names.append(portfolios['name'])
        #returns the portfolio names as list
        print("Portfolio_names:" + str(portfolio_names))
        return json.dumps(portfolio_names)
    except:
        return "No portfolios found."

#Deletes all unit test holdings and portfolios for cleanup
@app.route('/api/unit_test_delete',methods=['GET'])
def get_unit_test_delete():
    '''
    Deletes all portfolios and respective holdings that are of type 'unit test'
    '''
    portfolios = investmentportfolio.Get_Portfolios_by_Selector('type','unit test portfolio')['portfolios']
    print(portfolios)
    for p in portfolios:
        holdings = investmentportfolio.Get_Portfolio_Holdings(p['name'],False)
        # delete all holdings
        for h in holdings['holdings']:
            timestamp = h['timestamp']
            rev = h['_rev']
            investmentportfolio.Delete_Portfolio_Holdings(p['name'],timestamp,rev)
        investmentportfolio.Delete_Portfolio(p['name'],p['timestamp'],p['_rev']) 
    return "Portfolios deleted successfully."

#Calculates unit tests for a list of portfolios
@app.route('/api/unit_test',methods=['POST'])
def compute_unit_tests():
    '''
    Calculates analytics for a portfolio.
    Breaks into 500 instrument chunks to comply with container constraints.
    '''
    if request.method == 'POST':
        portfolios = []
        data = json.loads(request.data)
        portfolios.append(data["portfolio"])

    #Stopwatch
    start_time = datetime.datetime.now()
    if data:
        analytics = data["analytics"]
    else:
        analytics = ['THEO/Price','THEO/Value']
    results = []
    
    for p in portfolios:
        portfolio_start = datetime.datetime.now()
        holdings = investmentportfolio.Get_Portfolio_Holdings(p,False)['holdings']
        #Since the payload is too large, odds are there are 500-instrument chunks added to the portfolio.
        for ph in range(0,len(holdings)):
            instruments = [row['instrumentId'] for row in holdings[ph]['holdings']]
            print("Processing " + str(p) + " portfolio segment #"+str(ph) +".")
            #send 500 IDs at a time to Instrument Analytics Service:
            #for i in instruments...
            for i in range(0,len(instruments),500):
                ids = instruments[i:i+500]
                ia = instrumentanalytics.Compute_InstrumentAnalytics(ids,analytics)
                #for j in results...
                if 'error' not in ia:
                    for j in ia:
                        r = {
                            "portfolio":p,
                            "id":j['instrument']}
                        for a in analytics:
                            r[a] = j['values'][0][a]
                        r["date"] = j['values'][0]['date']
                        h = [row for row in holdings[0]['holdings'] if j['instrument']==row['instrumentId']][0]
                        for key,value in h.iteritems():
                            if key not in ['instrumentId']:
                                r[key] = value
                        results.append(r)
                #Debug
                if i+500<len(instruments):
                    l = i+500
                else:
                    l = len(instruments)
                print("Processed securities " + str(i) + " through " + str(l) + ". Time elapsed on this portfolio: " + str(datetime.datetime.now() - portfolio_start))

    print("Unit testing completed. Total time elapsed: " + str(datetime.datetime.now() - start_time))
    return Response(json.dumps(results), mimetype='application/json')

if __name__ == '__main__':
    app.run(host=host, port=port)