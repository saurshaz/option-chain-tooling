from flask import Flask, jsonify, request
import requests
import json
# import opstrat as op
from flask_cors import CORS
from jugaad_data.nse import NSELive
n = NSELive()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Home Page Route'


@app.route('/api/data')
def api():
    with open('data.json', mode='r') as my_file:
        text = my_file.read()
        return text

@app.route('/api/op')
def strat_op():
        c = request.args['c']
        print(c)
        res = requests.get("https://opstra.definedge.com/api/free/strategybuilder/payoff/{}".format(c))
        # res = requests.get("https://opstra.definedge.com/api/free/strategybuilder/payoff/{}".format('BANKNIFTY$+50x35400CEx12AUG2021x480.55x0x0&-50x35700CEx12AUG2021x236.22x0x0&+25x35500CEx18AUG2021x603.1x0x0&-50x35800CEx12AUG2021x160.13x0x0&+25x35600CEx18AUG2021x519.9x0x0$2021-08-12$0$0$0'))
        return jsonify(res.json())

@app.route('/api/prices')
def zero_prices():
    url = "https://kite.zerodha.com/oms/margins/orders"
    # /api/op?s=BANKNIFTY&q=25&st=36000&ty=CE&ex=21AUG2021&si=BUY&ot=MARKET&p=NRML&v=regular
    tradingsymbol = "{}{}{}{}".format(request.args['s'], request.args['ex'], request.args['st'], request.args['ty'])
    payload = [
	{
		"exchange": "NFO",
		"tradingsymbol": tradingsymbol,
		"transaction_type": request.args['si'],
		"variety": request.args['v'],
		"product": request.args['p'],
		"order_type": request.args['ot'],
		"quantity": float(request.args['q'])
	}
    ]
    # FIXME: the header shall be auto populated post zerodha sign-in and shall not be an input. OKAY for local setups, not for PRODUCTionalizing this.
    # passing vulnerability to the consumer of this API
    headers = {'authorization': 'enctoken {}'.format(request.headers['x-tok'])}
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    return jsonify(response.json())


@app.route('/api/oc')
def sym_price():
    q = n.stock_quote(request.args['s'])
    # return (jsonify(q['priceInfo']))
    # print("CE\tStrike\tPE")
    option_chain = n.index_option_chain("NIFTY")
    oc = {}
    for option in option_chain['filtered']['data']:
        # print("{}\t{}\t{}".format(option['CE']['lastPrice'], option['strikePrice'], option['PE']['lastPrice']))
        oc[option['strikePrice']] = {'CE': option['CE'], 'PE': option['PE']}
    return jsonify(oc)