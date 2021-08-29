from flask import Flask, jsonify, request, Response
import requests
import base64
import io
from io import BytesIO
import json
import opstrat as op
from flask_cors import CORS
from jugaad_data.nse import NSELive
from bokeh.plotting import ColumnDataSource, figure, output_file, show

import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# n = NSELive()
  

def check_optype(op_type):
    if (op_type not in ['p','c']):
        raise ValueError("Input 'p' for put and 'c' for call!")

def check_trtype(tr_type):
    if (tr_type not in ['b','s']):
        raise ValueError("Input 'b' for Buy and 's' for Sell!")  

def payoff_calculator(x, op_type, strike, op_pr, tr_type, n):
    y=[]
    if op_type=='c':
        for i in range(len(x)):
            y.append(max((x[i]-strike-op_pr),-op_pr))
    else:
        for i in range(len(x)):
            y.append(max(strike-x[i]-op_pr,-op_pr))
    y=np.array(y)

    if tr_type=='s':
        y=-y
    return y*n

def check_ticker(ticker):
    """
    Check ticker
    """
    try:
        return yf.Ticker('msft').info['currentPrice']
    except KeyError:
        raise ValueError('Ticker not recognized')

abb={'c': 'Call',
    'p': 'Put',
    'b': 'Long',
    's': 'Short'}

def multi_plotter(spot_range=20, spot=100,
                op_list=[{'op_type':'c','strike':110,'tr_type':'s','op_pr':2,'contract':1},
                {'op_type':'p','strike':95,'tr_type':'s','op_pr':6,'contract':1}], 
                  save=False, file='fig.png'):
    """
    Plots a basic option payoff diagram for a multiple options and resultant payoff diagram
    
    Parameters
    ----------
    spot: int, float, default: 100 
       Spot Price
       
    spot_range: int, float, optional, default: 20
       Range of spot variation in percentage 
       
    op_list: list of dictionary
       
       Each dictionary must contiain following keys
       'strike': int, float, default: 720
           Strike Price
       'tr_type': kind {'b', 's'} default:'b'
          Transaction Type>> 'b': long, 's': short
       'op_pr': int, float, default: 10
          Option Price
       'op_type': kind {'c','p'}, default:'c'
          Opion type>> 'c': call option, 'p':put option
       'contracts': int default:1, optional
           Number of contracts
    
    save: Boolean, default False
        Save figure
    
    file: String, default: 'fig.png'
        Filename with extension
    
    Example
    -------
    op1={'op_type':'c','strike':110,'tr_type':'s','op_pr':2,'contract':1}
    op2={'op_type':'p','strike':95,'tr_type':'s','op_pr':6,'contract':1}
    
    import opstrat  as op
    op.multi_plotter(spot_range=20, spot=100, op_list=[op1,op2])
    
    #Plots option payoff diagrams for each op1 and op2 and combined payoff
    
    """
    x=spot*np.arange(100-spot_range,101+spot_range,0.01)/100
    y0=np.zeros_like(x)         
    
    y_list=[]
    for op in op_list:
        op_type=str.lower(op['op_type'])
        tr_type=str.lower(op['tr_type'])
        check_optype(op_type)
        check_trtype(tr_type)
        
        strike=op['strike']
        op_pr=op['op_pr']
        try:
            contract=op['contract']
        except:
            contract=1
        y_list.append(payoff_calculator(x, op_type, strike, op_pr, tr_type, contract))
    

    def hover(event):
        txt.set_text("ss")

    def plotter():
        y=0
        plt.figure(figsize=(10,6))


        for i in range (len(op_list)):
            try:
                contract=str(op_list[i]['contract'])  
            except:
                contract='1'
                
            label=contract+' '+str(abb[op_list[i]['tr_type']])+' '+str(abb[op_list[i]['op_type']])+' ST: '+str(op_list[i]['strike'])
            # sns.lineplot(x=x, y=y_list[i], label=label, alpha=0.5)
            y+=np.array(y_list[i])
        
        


        # import pdb; pdb.set_trace()
        plt.legend(loc='upper right')
        plt.title("Multiple Options Plotter")
        plt.fill_between(x, y, 0, alpha=0.2, where=y>y0, facecolor='green', interpolate=True)
        plt.fill_between(x, y, 0, alpha=0.2, where=y<y0, facecolor='red', interpolate=True)
        sns.lineplot(x=x, y=y, label='combined', alpha=1, color='k')
        plt.axhline(color='k', linestyle='--')
        plt.axvline(x=spot, color='r', linestyle='--', label='spot price')
        plt.tight_layout()
        output_file("toolbar.html")
        if save==True:
            plt.savefig(file)
        plt.show()


        # # Save it to a temporary buffer.
        # buf = BytesIO()
        # plt.savefig(buf, format="png")
        # # Embed the result in the html output.
        # data = base64.b64encode(buf.getbuffer()).decode("ascii")
        # return f"<img src='data:image/png;base64,{data}'/>"

        # def create_figure():
        #     fig = Figure()
        #     axis = fig.add_subplot(1, 1, 1)
        #     xs = range(100)
        #     ys = [random.randint(1, 50) for x in xs]
        #     axis.plot(xs, ys)
        #     return fig
        # fig = create_figure()
        # output = io.BytesIO()
        # FigureCanvas(fig).print_png(output)
        # return Response(output.getvalue(), mimetype='image/png')


    return plotter()   

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


@app.route('/api/payoff')
def opt_payoff():
    op1={'op_type': 'c', 'strike': 215, 'tr_type': 's', 'op_pr': 7.63}
    op2={'op_type': 'c', 'strike': 220, 'tr_type': 'b', 'op_pr': 5.35}
    op3={'op_type': 'p', 'strike': 210, 'tr_type': 's', 'op_pr': 7.20}
    op4={'op_type': 'p', 'strike': 205, 'tr_type': 'b', 'op_pr': 5.52}
    op_list=[op1, op2, op3, op4]
    return multi_plotter(spot=212.26,spot_range=10, op_list=op_list)

    # return jsonify({"Flask":"Charts"})