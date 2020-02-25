import json, boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import random

def lambda_handler(event, context):
    sqs_client = boto3.client('sqs')
    
    try:
        # polls a message from the SQS queue
        response = sqs_client.receive_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/974283779235/DiningQueue',
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1
        )
        
        sqs_client.delete_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/974283779235/DiningQueue',
            ReceiptHandle=response['Messages'][0]['ReceiptHandle']
        )
    except KeyError:
        return {
            'statusCode': 404,
            'body': "Empty SQS Queue."
        }
    
    # this is the data we need
    restaurant_requirements = response['Messages'][0]['MessageAttributes']
    cuisine_type = restaurant_requirements['Cuisine']['StringValue'].lower()
    people_number = restaurant_requirements["PeopleNumber"]["StringValue"]
    time = restaurant_requirements["DiningTime"]["StringValue"]
    phone_number = restaurant_requirements["PhoneNumber"]["StringValue"]
    
    
    host = 'search-nyc-restaurants-3xe6tomp3hbigddvvoja4qvmxq.us-east-1.es.amazonaws.com' 
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    result = es.search(index="restaurants", body={"query": {"match":{"cuisine": cuisine_type}}})
    restaurants_that_match_cuisine_type = result['hits']['hits']
    
    dynamodb_client = boto3.client('dynamodb')
    restaurant_data = []
    
    # get info on the first three results returned by elasticsearch
    for restaurant_num in [0,1,2]:
        res_id = restaurants_that_match_cuisine_type[restaurant_num]['_id']
        res_details = dynamodb_client.get_item(
            TableName='yelp-restaurants',
            Key={'id':{'S':str(res_id)}}
        )
        restaurant_data.append(res_details)

    text_message = "Hello! Here are my " + cuisine_type + " restaurant suggestions for "
    text_message += people_number + " people for today at " + time + ":\n"
    
    for r in restaurant_data:
        name = r['Item']['name']['S']
        address = r['Item']['address']['S']
        text_message += name + ", located at " + address +"\n"

    text_message += "Enjoy your meal!"
    
    sns_client = boto3.client('sns')

    response = sns_client.publish(
        PhoneNumber="+" + phone_number,
        Message=text_message,
    )
    
    return {
        'statusCode': 200,
        'body': text_message
    }
