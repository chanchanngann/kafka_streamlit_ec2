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
1. Create a s3 bucket to store data in advance: let say **my-stock-bucket**

2. Launch EC2 using the cloudformation template.
	- You need to edit the template by inputing your key pair to SSH into EC2. I am using **rachel.pem** here.
 	- For the sake of easy implementation, IP 0.0.0.0/0 is entered for **SSHLocation** parameter. It'd be better to use your own IP instead.

```aws cloudformation create-stack --stack-name kafka-streamlit-dashb --template-body file:///Users/somewhere/ec2_cfn_template.yaml --capabilities CAPABILITY_NAMED_IAM```


3. Get the public IP of EC2 on AWS concole and SSH into EC2 using the public IP (let say EC2 public IP = ```12.34.56.78```)

```
ssh -i rachel.pem ec2-user@12.34.56.78
```

4. In the meanwhile, upload the required files to EC2.
You may want to edit kickoff.sh in advance for the following variables.
AWS_DEFAULT_REGION,KAFKA_TOPIC,TICKER

```
scp -i rachel.pem kafka/kickoff.sh ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/requirements.txt ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/producer.py ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/consumer.py ec2-user@12.34.56.78:~/.
scp -i rachel.pem kafka/stock_app.py ec2-user@12.34.56.78:~/.
```
5. Run **kickoff.sh** in EC2 shell, you will need to enter 2 arguments: EC2 public IP & S3 bucket name

```
cd ~
chmod 744 ./kickoff.sh
./kickoff.sh 12.34.56.78 my-stock-bucket
```

##### What does kickoff.sh do here?
- download and install kafka
- install python3.8
- set up python virtual environment 
- install all the required packages/dependencies
- increase memory for the kafka server
- edit Kafka server.properties
- kick off zookeeper & kafka server
- create kafka topic 
- start kafka producer & consumer to ingest real-time data on a time interval of 10mins
- configure aws default region for streamlit app (I am using **ap-northeast-2**)
- kick off streamlit app

##### Job status check
Since all scripts are runnning in the background, you can check the status as below.

```ps -e -f | grep python```

You should see 3 .py scripts are in ```running``` status. (producer.py, consumer.py, stock_app.py) Otherwise, there should be error in executing **kickoff.sh**.

5. Go to Athena, create the required table. 
(remarks: Since this is a partitioned table, we need to add partition to Athena whenever a new partition is produced at S3. this is handled in **stock_app.py**)


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

6. The infrastructure is done, go check for the result~
  - In the specified S3 bucket, data (in parquet format) should be ingested on a regular time interval of 10mins.
	  Same filename is being used during data ingestion, so data will only be updated instead of being appended.
	  As I dont need accumulated data for the same date and I just want the most updated data for each date.

![aws architecture](/s3.PNG)
  
  - At Athena, we can query the data in S3.

```
  select * from rachel.stock1;
```

![aws architecture](/athena.PNG)

   - Go to the browser and enter the URL ```12.34.56.78:8501```, the streamlit dashboard will show up.
     Prior to feeding real-time data, I pulled recent 3 months of data and save them in S3. 
     Thus we can review the price trend of Kakaopay for the recent 3 months in a line chart.

![aws architecture](/streamlit_dashb.PNG)

### Notes
1. In the EC2 security group -> inbound rule setting, we need to add the following ports.
   The security group setting has been included in the cloudformation template already.
    - port 22 - for SSH 
    - port 2181 - for zookeeper
    - port 9092 - for Kafka server
    - port 8501 - for Streamlit
	
2. Since we will access S3 and Athena in this project, we need to create IAM role for EC2 and give access for the 2 resources.
   The IAM role setting has been included in cloudformation template already.

3. Everytime you refresh the streamlit app, data is fetched by running query against Athena. You can find the history in Athena's *recent queries* tab.

### Reference
- https://github.com/darshilparmar/stock-market-kafka-data-engineering-project
- https://aws.amazon.com/blogs/opensource/using-streamlit-to-build-an-interactive-dashboard-for-data-analysis-on-aws/
- https://techviewleo.com/how-to-install-python-on-amazon-linux/
- https://github.com/upendrak/streamlit-aws-tutorial
- https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart
- https://plotly.com/python/line-charts/
