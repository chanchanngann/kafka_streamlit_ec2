#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Please provide 2 arguments: EC2 public IP and S3 bucket name"
  exit 1
fi

stack_name=kafka-streamlit-dashb

# Manual entry (edit this part)
EC2_PUBLIC_IP=$1 
AWS_DEFAULT_REGION=ap-northeast-2
KAFKA_TOPIC=kakaopay
TICKER="377300.KS"

# pls create the bucket at AWS S3 in advance
S3_BUCKET_NAME=$2 #${stack_name}

echo "stack name=${stack_name}"
echo "bucket name=${S3_BUCKET_NAME}" 
echo "region=${AWS_DEFAULT_REGION}"

echo "Download and install Kafka"

wget https://downloads.apache.org/kafka/3.5.0/kafka_2.12-3.5.0.tgz
tar -xvf kafka_2.12-3.5.0.tgz 
sudo yum install java-1.8.0-openjdk

echo "Install python3.8"
sudo yum install -y amazon-linux-extras
sudo amazon-linux-extras enable python3.8
sudo yum install python3.8

echo "Create Python virtual env"
python3 -m pip install --upgrade pip
python3.8 -m venv vvenv
source vvenv/bin/activate

echo "Download and install from requirements.txt"
pip install -r requirements.txt

#increase memory for the kafka server (since we are using single ec2 machine)
echo "Increase memory for the kafka server"
export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"

#Edit Kafka server.properties so that Kafka will point to public IP of EC2
echo "Edit Kafka server.properties"
cd kafka_2.12-3.5.0
kafka_config_file=config/server.properties
sed -i -e "s #advertised.listeners=PLAINTEXT://your.host.name:9092 advertised.listeners=PLAINTEXT://${EC2_PUBLIC_IP}:9092 g" ${kafka_config_file}

echo "Kick off zookeeper"
bin/zookeeper-server-start.sh -daemon config/zookeeper.properties
sleep 2

echo "Kick off Kafka-server"
bin/kafka-server-start.sh -daemon config/server.properties
sleep 2

echo "Create Kafka topic"
bin/kafka-topics.sh --create --topic "${KAFKA_TOPIC}" --bootstrap-server "${EC2_PUBLIC_IP}":9092 --replication-factor 1 --partitions 1 
sleep 15

echo "Downloading and loading the data into S3"
cd ..
S3_BUCKET_NAME=$(echo "$S3_BUCKET_NAME" | awk '{print tolower($0)}') # must be lower case for s3

#aws s3 mb s3://${S3_BUCKET_NAME} > /dev/null

echo "Start consumer.py"
source vvenv/bin/activate
python3 ~/consumer.py -i "${EC2_PUBLIC_IP}" -p "${KAFKA_TOPIC}" -b "${S3_BUCKET_NAME}" > /dev/null &
sleep 2

echo "Start producer.py"
source vvenv/bin/activate
python3 ~/producer.py -i "${EC2_PUBLIC_IP}" -p "${KAFKA_TOPIC}" -t "${TICKER}" > /dev/null &
sleep 2

echo "Set up aws region for the streamlit app"
source vvenv/bin/activate
aws configure set region ${AWS_DEFAULT_REGION}
streamlit run ~/stock_app.py > /dev/null &
sleep 2

echo "You can view your Streamlit app in your browser. Just go to ${EC2_PUBLIC_IP}:8501"
