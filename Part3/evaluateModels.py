import boto3
from datetime import datetime
from datetime import timedelta
import time
import json
import pymysql
import urllib.request


#NOTE:  This is a helper function that will parse and return JSON
#from an event message body.  I have found this addresses various 
#scenarios where messages have slightly different formats between
#production SQS and using the Test functionality.
def parse_message_body_json(message_body):
    
    message_body_json=None
    
    try:
        #Adjust our message body so that it parses correctly\
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
            
            message_body=json.loads(str(message_body))
            
            message_body_json=message_body[0]
    except Exception as error:
        print(error)
        print("Unable to parse JSON.")
    
    return message_body_json
    
        

def lambda_handler(event, context):
    
    #Store recommendations here to return from the function.
    arr_buy_recommendations=[]
        
    print("Connecting to DB...")
    #Setup our database connection
    db_host="<Your DB hostname here>"
    db_username="crypto"    #OR whatever DB username you created
    db_password="<Your DB password here>"
    conn = pymysql.connect(host=db_host, user=db_username, password=db_password, \
        charset='utf8', db='aither_crypto', cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    
    
    print("Parsing symbol/price information from the event object...")
    message_body_json=parse_message_body_json(event)
    print(message_body_json)
    
    print("Getting pool and model combinations for the symbol...")
    sql = """select 
              p.pool_id,
              m.model_id,
              m.exchange,
              m.symbol,
              p.total_amount as 'total_pool_amount',
              m.proc_name_buy
            from
              trading_models m,
              trading_pools p,
              trading_pool_models pm
            where
              m.enabled = 1
                and p.symbol='%s'
                and p.exchange = m.exchange
            and p.symbol = m.symbol
            and pm.pool_id=p.pool_id
            and pm.model_id=m.model_id;""" % message_body_json["Symbol"]
    #print(sql)
    cur.execute(sql)
    
    result_models = cur.fetchall()

    
    #Evaluate BUY opportunities for each pool/model configuration
    print("Evaluating BUY opportunities...")
    for row in result_models:
        try:
            timestamp=message_body_json["Timestamp"]
            
            print("Evaluating symbol %s at %s against model %s..." % (message_body_json["Symbol"], timestamp, row["model_id"]))
            
            sql = "call %s('%s', '%s');" % (row["proc_name_buy"], timestamp, row["model_id"])
            print(sql)
            
            cur.execute(sql)
        
            eval_result = cur.fetchall()
            
             # If a row is returned from the proc, then that means we want to BUY.
            for eval_row in eval_result:
                print("TODO:  Placing a BUY order for model=%s..." % (row["model_id"]))
                
                arr_buy_recommendations.append({"model_id":row["model_id"]})
                
                #TODO:  Execute Trade Here
                
        except Exception as error:
            print(error)
            continue

    
    #Clean up
    cur.close()
    conn.close()
    

    #Return result 
    return {
        'data': message_body_json,
        'buy_recommendations': arr_buy_recommendations
    }
