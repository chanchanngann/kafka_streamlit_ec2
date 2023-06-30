from kafka import KafkaConsumer
from time import sleep
from json import dumps,loads
import json
#from s3fs import S3FileSystem
from datetime import datetime
#import talib as ta
import pandas as pd
import awswrangler as wr
import argparse

# Parse command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("-i", "--ec2_public_ip", help="ec2 public ip")
argParser.add_argument("-p", "--topic", help="Kafka topic name")
argParser.add_argument("-b", "--bucket", help="S3 raw bucket")
args = argParser.parse_args()

# set up parameters
EC2_PUBLIC_IP = args.ec2_public_ip
TOPIC = args.topic
RAW_BUCKET = args.bucket

def main():

    #today=datetime.today().strftime("%Y%m%d")
    consumer = KafkaConsumer(
         TOPIC,
         bootstrap_servers=[f'{EC2_PUBLIC_IP}:9092'], 
         value_deserializer=lambda x: loads(x.decode('utf-8')))

    print('created consumer')

    #realtime output to S3 bucket
    for count, i in enumerate(consumer):
        dt = i.value.get('Date').replace('-','')
        df = pd.json_normalize(i.value)
        wr.s3.to_parquet(df,path=f"s3://{RAW_BUCKET}/{TOPIC}/dt={dt}/{dt}_{TOPIC}_stock.parquet")
        print(f"done upload {count}")

if __name__ == "__main__":
    main()
