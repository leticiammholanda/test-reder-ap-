import pandas as pd
import json
import requests
import os
from flask import Flask, request,Response

#CONSTANTES
TOKEN= '6084558382:AAEzq3uupKlRzE28001-EkeM9bDXK3_flR4'
##info do bot
#https://api.telegram.org/bot6084558382:AAEzq3uupKlRzE28001-EkeM9bDXK3_flR4/getMe

##get updates
#https://api.telegram.org/bot6084558382:AAEzq3uupKlRzE28001-EkeM9bDXK3_flR4/getUpdates

##send message 
#https://api.telegram.org/bot6084558382:AAEzq3uupKlRzE28001-EkeM9bDXK3_flR4/sendMessage?chat_id=1657664817&text=Hi Letícia, I am doing good,tks!

def send_message( chat_id, text ):
    url='https://api.telegram.org/bot{}'.format(TOKEN)
    url= url + 'sendMessage?chat_id={}'.format( chat_id)
    
    requests.post(url, json={'text':text})
    print('Status Code {}'.format( r.status_code ) )
    
    return None
    


def load_dataset(store_id):    
    #loading dataset
    df10 = pd.read_csv( 'test.csv' )
    df_store = pd.read_csv( 'store.csv' )

    #merge test dataset +store
    df_test = pd.merge(df10,df_store, how='left', on='Store')

    #chose store for predict
    df_test= df_test[df_test['Store']==store_id]
    
    if not df_test.empaty:
        #remove cloased days 
        df_test  = df_test[df_test['Open'] != 0]
        df_test  = df_test[~df_test['Open'].isnull()]
        df_test =  df_test.drop( 'Id', axis=1 )

        #convertendo to json
        data = json.dumps(df_test.to_dict(orient='records'))
        
    else:
        data='error'
        

    return data

def predict(data):
    #API call

    url = 'https://teste-rossmann-api-ihe9.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json' }

    data = data

    r = requests.post(url, data=data, headers = header )
    print('Status Code{}'.format(r.status_code))


    d1=pd.DataFrame(r.json(), columns = r.json()[0].keys())
    
    return d1


def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text'] 
    
    store_id = store_id.replace( '/','' )
    
    try:
        store_id = int( store_id )
        
    except ValueError:
        
        store_id = 'error'
        
    
    
    return chat_id, store_id

#API initialize
app = Flask( __name__ )

@app.route('/',methods=['GET','POST'] )
def index():
    if request.method == 'POST':
        message = request.get_jason()
        
        chat_id, store_id = parse_message( message )
        
        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)
            
            if data != 'error':
                #prediction
                d1 = predict( data )
                #calculation
                d2= d1[['store', 'prediction']].groupby('store').sum().reset_index()
                
                #send message
                msg = 'Store Number{} will sell R$ {:,.2f} in the next 6 weeks'.format(
                           d2['store'].values[0],
                           d2['prediction'].values[0] ) 
                
                send_message( chat_id, msg )
                return Response( 'OK',status=200 )

                
            
            else:
                send_message(chat_id, 'Store not Available')
                return Response( 'OK', status=200 )
                

        else:
            send_message(chat_id, 'Store ID is Wrong' )
            return Response('OK', status = 200 )
        
        
    else:
        return '<h1> Rossmann Telegram BOT </h1>'
    

if __name__ == '__main__':
#    port=os.enciron.get('PORT',5000)
    app.run( host='0.0.0.0', port=5000 )
