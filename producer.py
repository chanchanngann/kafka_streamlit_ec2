import pandas as pd
from kafka import KafkaProducer
from time import sleep
from json import dumps
import json
import argparse
import yfinance as yf
from datetime import datetime
import pytz

# Parse command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("-i", "--ec2_public_ip", help="ec2 public ip")
argParser.add_argument("-p", "--topic", help="Kafka topic name")
argParser.add_argument("-t", "--ticker", help="Yahoo Finance Ticker name")
args = argParser.parse_args()

# set up parameters
EC2_PUBLIC_IP = args.ec2_public_ip
TOPIC = args.topic
TICKER = args.ticker
KST = pytz.timezone("Asia/Seoul")

def main():

    producer = KafkaProducer(bootstrap_servers=[f'{EC2_PUBLIC_IP}:9092'], #put EC2 public ip here
                             value_serializer=lambda x: 
                             dumps(x).encode('utf-8'))
    print ("created producer")
    
    #i = 1
    while True:
        #realtime data input
        time_now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] #valid timestamp literal at athena: TIMESTAMP '2001-08-22 03:04:05.321'
        stock = yf.Ticker(TICKER)
        #data = stock.history(period='3mo')
        data = stock.history(period='1d')
        
        #data wrangling
        data = data.reset_index()
        data['Date'] = data.Date.astype(str).str[:10]
        data['stock_name'] = TOPIC
        data['ticker'] = TICKER
        data['last_updated'] = time_now

        #send 3 mths data
        #dict_stock = data.to_dict(orient="records")
        #for i in range(len(dict_stock)):
        #    producer.send(TOPIC, value=dict_stock[i])

        #send 1d data
        dict_stock = data.to_dict(orient="records")[0]
        producer.send(TOPIC, value=dict_stock)
        print("data sent")
        producer.flush()
        #i += 1

        sleep(600) #10min interval

if __name__ == "__main__":
    main()