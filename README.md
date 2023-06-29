# Kafka and Streamlit Dashboard on EC2 to review real-time stock trend

## Goal
My goal of this project is to learn Kafka & Streamlit and try to deploy this combo on AWS EC2.
The data source is real-time stock data feeding by Yahoo Finance API.
The outcome will be shown on Streamlit dashboard -> a simple price trend of the stock I am recently interested in: Kakaopay.

## Architecture
1. With Kafka, real-time stock data is being pulled from Yahoo Finance API every 10 mins and stored at S3.
2. Table is first created at Athena, data stored in S3 can be analysed in Athena in real-time.
3. By using awswrangler library, we can send SQL query to Athena and fetch the data we want. 
   Outcome can be visualized on streamlit dashboard directly.

![aws architecture](/architecture.png)

## Steps
1. Launch EC2 using the cloudformation template

```aws cloudformation create-stack --stack-name kafka-streamlit-dashb --template-body file:///Users/somewhere/ec2_cfn_template.yaml --capabilities CAPABILITY_NAMED_IAM```

2. SSH into EC2 using EC2 public IP (let say the EC2 public IP = ```12.34.56.78```)

```
ssh -i rachel.pem ec2-user@12.34.56.78
```

3. In the meanwhile, upload the required files to EC2.
You may need to edit kickoff.sh file in advance for the following variables.
AWS_DEFAULT_REGION,KAFKA_TOPIC,TICKER,S3_BUCKET_NAME

```
scp -i rachel.pem kafka/prd/kickoff.sh ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/prd/requirements.txt ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/prd/producer.py ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/prd/consumer.py ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/prd/stock_app.py ec2-user@12.34.56.78:~/.
```
4. Run the kickoff script in EC2 shell, you will be prompted to enter EC2 public IP.

```
cd ~
chmod 744 ./kickoff.sh
./kickoff.sh
```

##### What does kickoff.sh do here?
- install python3.8
- set up python virtual environment 
- install all the required packages/dependencies
- donwload and install kafka
- kick off zookeeper followed by kafka server
- create kafka topic 
- start kafka producer & consumer to ingest real-time data
- configure aws default region
- kick off streamlit app
	
5. Go to Athena, create the required table. 
(remarks: Since this is a partitioned table, we need to add partition to Athena whenever a new partition is created at S3.)


```
CREATE DATABASE rachel;

CREATE EXTERNAL TABLE IF NOT EXISTS `rachel`.`stock1`(
`date` STRING, 
`open` DOUBLE, 
`high` DOUBLE, 
`low` DOUBLE, 
`close` DOUBLE, 
`volume` INT, 
`dividends` DOUBLE, 
`stock_splits` DOUBLE, 
`stock_name` STRING, 
`ticker` STRING, 
`last_updated` STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
 's3://my-stock-bucket/kakaopay/'
TBLPROPERTIES ('skip.header.line.count'='1','classification'='parquet', 'useGlueParquetWriter'='true');

MSCK REPAIR TABLE rachel.stock1;
```

6. The infrastructure is done, check for the result
  - In the specified S3 bucket, data (in parquet format) should be ingested on a regular time interval of 10mins.
	  Same filename is being used during data ingestion, so data will only be updated instead of being appended.
	  As I dont need accumulated data for the same date and I just want the most updated price for each date.
	  
  - At Athena, we can query the data in S3.

```
  select * from rachel.stock1;
```
   - Go to the browser and enter the URL ```12.34.56.78:8501```, the streamlit dashboard will show up.
     Prior to feeding real-time data, I pulled recent 3 months of data and save them in S3. 
     Thus we can review the price trend of Kakaopay for the recent 3 months in a line chart.

![aws architecture](/streamlit_dashb_1.PNG)
 
### Notes
1. In the EC2 security group -> inbound rule setting, we need to add the following ports.
   The security group setting is included in the cloudformation template.
    - port 22 - for SSH 
    - port 2181 - for zookeeper
    - port 9092 - for Kafka server
    - port 8501 - for Streamlit
	
2. Since we will access S3 and Athena in this project, we need to create IAM role for EC2 and give access for the 2 resources.
   The IAM role setting is included in cloudformation template.

### Reference
- https://github.com/darshilparmar/stock-market-kafka-data-engineering-project
- https://aws.amazon.com/blogs/opensource/using-streamlit-to-build-an-interactive-dashboard-for-data-analysis-on-aws/
- https://techviewleo.com/how-to-install-python-on-amazon-linux/
- https://github.com/upendrak/streamlit-aws-tutorial
- https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart
- https://plotly.com/python/line-charts/
