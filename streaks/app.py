import boto3
from datetime import datetime
import json 

db = boto3.resource('dynamodb')
sqs = boto3.resource('sqs', region_name='us-east-1')


def app(event, context):
    streaks = db.Table('post_streaks')
    for event in event['Records']:
        body = json.loads(event['body'])
        # print(body['Message'])
        print("Received event: " + str(event))
        message = json.loads(body['Message'])

        try:
            now = str(datetime.now())
            user_id = message['user_id']
            released_timestamp_int = message['released_timestamp']
            upload_timestamp_int = message['upload_timestamp']
            is_late = upload_timestamp_int - released_timestamp_int > 120

            # convert to days
            released_day = released_timestamp_int // 86400
            upload_day = upload_timestamp_int // 86400
            # print(f'release days {released_day}')
            last_post_info = get_last_post_info(user_id, released_timestamp_int)
            # print(f'last_post_info  {last_post_info}')
            last_post_day = last_post_info.get('last_post_day', released_day)
            current_streak = last_post_info.get('streak', 0)

            if released_day - last_post_day == 1:
                current_streak += 1
            else:
                current_streak = 1 # Reset streak if more than a day has passed

            res = streaks.put_item(
                Item={'upload_timestamp_int': upload_timestamp_int, 
                      'user_id': user_id, 
                      'is_late': is_late, 
                      'released_timestamp_int': released_timestamp_int, 
                      'load_dt': now,
                      'streak': current_streak
                      }) 
            # print(f'Streaks table load successful: {res}')
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Load successful'})
            }
        except Exception as e:
            print(f'Streaks table load failed: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Load failed'})
            }
        
            
        sqs.delete_messages(
            queue_url='https://sqs.us-east-1.amazonaws.com/851725573367/PostStreaksQueue', 
            ReceiptHandle= body['ReceiptHandle'])
        # print(f'Message {body["MessageId"]} deleted from queue')

def get_last_post_info(user_id, current_released_timestamp_int):
    streaks = db.Table('post_streaks')

    response = streaks.query(
        KeyConditionExpression='user_id = :user_id AND released_timestamp_int < :current_ts',
        ExpressionAttributeValues={
            ':user_id': user_id,
            ':current_ts': current_released_timestamp_int
        },
        ScanIndexForward=False,  
        Limit=1  
    )

    # print(f'last record {response}')
    
    items = response.get('Items', [])
    if items:
        last_post = items[0]
        last_post_day = last_post['released_timestamp_int'] // 86400
        current_streak = last_post.get('streak', 0)
        return {'last_post_day': last_post_day, 'streak': current_streak}
    else:
        # Return default values if no previous post exists
        return {'last_post_day': 0, 'streak': 0}