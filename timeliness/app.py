import boto3
from datetime import datetime
import json 

db = boto3.resource('dynamodb')
sqs = boto3.resource('sqs', region_name='us-east-1')


def app(event, context):
    # Load timeliness table with current timestamp and user_id.
    # If the upload timestamp is more than 2 minutes later than the released timestamp, then the user is late.
    # The released timestamp is the timestamp when the app prompts the user to upload a picture.
    # The upload timestamp is the timestamp when the user uploads the file.
    # The user_id is the user's unique identifier.
    # The is_late flag is set to True if the upload timestamp is more than 2 minutes later than the released timestamp.
    timeliness = db.Table('post_timeliness')
    for event in event['Records']:
        body = json.loads(event['body'])
        # print(body['Message'])
        message = json.loads(body['Message'])

        try:
            now = str(datetime.now())
            user_id = message['user_id']
            released_timestamp_int = message['released_timestamp']
            upload_timestamp_int = message['upload_timestamp']
            is_late = upload_timestamp_int - released_timestamp_int > 120
            res = timeliness.put_item(
                Item={'upload_timestamp_int': upload_timestamp_int, 
                      'user_id': user_id, 
                      'is_late': is_late, 
                      'released_timestamp_int': released_timestamp_int, 
                      'load_dt': now
                      }) 
            print(f'Timeliness table load successful: {res}')
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Load successful'})
            }
        except Exception as e:
            print(f'Timeliness table load failed: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Load failed'})
            }

        sqs.delete_messages(
            queue_url='https://sqs.us-east-1.amazonaws.com/851725573367/PostTimelinessQueue', 
            ReceiptHandle= body['ReceiptHandle'])
        print(f'Message {body["MessageId"]} deleted from queue')