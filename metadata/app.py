import boto3
import json 

db = boto3.resource('dynamodb')
sqs = boto3.resource('sqs', region_name='us-east-1')

def app(event, context):
    metadata = db.Table('post_metadata')
    for event in event['Records']:
        body = json.loads(event['body'])
        print(body['Message'])
        message = json.loads(body['Message'])
        print(message)

        try:
            user_id = message['user_id']
            released_timestamp_int = message['released_timestamp']
            upload_timestamp_int = message['upload_timestamp']
            res = metadata.put_item(
                Item={'user_id': user_id,
                'released_timestamp_int': released_timestamp_int,
                'upload_timestamp_int': upload_timestamp_int
                })
            print(f'Metadata table load successful: {res}')
            print(f"processed user : {user_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Load successful'})
            }

        except Exception as e:
            print(f'Metadata table load failed: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Load failed'})
            }
        
        sqs.delete_messages(
            queue_url='https://sqs.us-east-1.amazonaws.com/851725573367/PostMetadataQueue', 
            ReceiptHandle=body['ReceiptHandle']
            )
        print(f'Message {body["MessageId"]} deleted from queue')
