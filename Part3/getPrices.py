import json
import boto3
from urllib.request import Request, urlopen
from datetime import datetime
import pymysql

#NOTE:  This is a helper function that will parse and return JSON
#from an event message body.  I have found this addresses various 
#scenarios where messages have slightly different formats between
#production SQS and using the Test functionality.
def parse_message_body_json(message):
    
    message_body_json=None
    
    try:
        #Adjust our message body so that it parses correctly
        message_body=message["body"]
        
        if isinstance(message_body, list)==True:
            list_message_body=message['body']
            
            message_body_json = convert_list_to_dict(list_message_body)[0]
            
        elif isinstance(message_body, dict)==True:
            message_body_json=message_body
        
        elif isinstance(message_body, str):
            message_body=message_body.replace("'", "\"")
            message_body=message_body.strip('"')
            
            if message_body.index('[')!=0:
                if message_body.rindex(']')!=len(message_body)-1:
                    message_body="[%s]" % message_body
            
            #print("Debug 1: %s" % str(message_body))
            
            message_body=json.loads(str(message_body))
            
            message_body_json=message_body[0]
            
            
        #print(message_body)
        
    except Exception as error:
        print(error)
        print("Unable to parse JSON.")
        
        #pass
    
    return message_body_json


#The main handler for this Lambda function.   
def lambda_handler(event, context):

    symbols = []
    json_return=[]
    
    #Setup our database connection
    db_host="<Your DB hostname here>"
    db_username="crypto"    #OR whatever DB username you created
    db_password="<Your DB password here>"
    conn = pymysql.connect(host=db_host, user=db_username, password=db_password, \
        charset='utf8', db='aither_crypto', cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    
    #Verify we have event records and then parse each one.
    if "Records" in event:
        for message in event['Records']:
            print("Processing message...; message=%s" % message)
            
            message_body_json=parse_message_body_json(message)
            
            print(message_body_json)
            
            symbols.append(message_body_json["Symbol"])
        
      
    print(symbols)   
    
    #Format date to send in the TIMESTAMP field
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    #For each symbol (coin_pair) in our event message, retrieve the price.
    for coin_pair in symbols:
        url_spot="https://api.coinbase.com/v2/prices/%s/spot" % (coin_pair)
        
        try:
            #Get SPOT price
            req = Request(url_spot)
            req.add_header('Accept', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urlopen(req, timeout = 15) as response:
                raw_json = response.read()
                
                spot_details=json.loads(raw_json)

            #Store the results in RDS
            sql = """insert into price_history (exchange, symbol, created, price)
                    values ('COINBASE', '%s', '%s', %s)""" % (coin_pair, now, spot_details['data']['amount'])
            print(sql)
            cur.execute(sql)
            conn.commit()
            
            #Store the result into JSON.  We will return this for now, but use it later.
            arr_single_coin=[]
            dict_single_coin={"Symbol": coin_pair, "Price": spot_details['data']['amount'], "Timestamp":now}
            arr_single_coin.append(dict_single_coin)
            
            lambda_client = boto3.client('lambda')
            evaluateModels_response = lambda_client.invoke(FunctionName="evaluateModels",
                                                  InvocationType='RequestResponse',
                                                  Payload=json.dumps(dict_single_coin))
            
            payload=evaluateModels_response['Payload']
            payload_json=json.loads(payload.read().decode("utf-8"))
            
            print(payload_json)
            
            json_return.append(arr_single_coin)
                
        except Exception as error:
            print("ERROR:  Failed to retrieve prices for %s" % coin_pair)
            print(error)
        
            
    #Return result 
    return {
        'statusCode': 200,
        'body': json_return
    }
