import json, boto3

def lambda_handler(event, context):
    location = event["currentIntent"]["slots"]["Location"].title()
    cuisine = event["currentIntent"]["slots"]["Cuisine"].title()
    dining_time = event["currentIntent"]["slots"]["DiningTime"].title()
    people_number = event["currentIntent"]["slots"]["PeopleNumber"].title()
    phone_number = event["currentIntent"]["slots"]["PhoneNumber"].title()
    
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/974283779235/DiningQueue'

    response = sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds = 10,
        MessageAttributes = {
            'Location': {
                'DataType': 'String',
                'StringValue': location
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'DiningTime': {
                'DataType': 'String',
                'StringValue': str(dining_time)
            },
            'PeopleNumber': {
                'DataType': 'Number',
                'StringValue': people_number
            },
            'PhoneNumber': {
                'DataType': 'Number',
                'StringValue': phone_number
            },
        },
        MessageBody=(
            'Information for dining suggestions.'
        )
    )
    
    response = {
                "dialogAction":
                    {
                     "fulfillmentState":"Fulfilled",
                     "type":"Close",
                     "message":
                        {
                          "contentType":"PlainText",
                          "content": "I've received your request and "
                           + "I'll notify you over text once I've generated the list of restaurant suggestions."
                        }
                    }
                }
    return response