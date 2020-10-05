# Working with flask, celery and Nexmo
import time, bson, json, os, sys, datetime, string, random
from bson import ObjectId
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import dns

from flask import Flask, request, jsonify
from celery import Celery
import nexmo


import sys, os, time
# Accessing files in directories
if getattr(sys, 'frozen', False):
    # running in a bundled form
    base_dir = sys._MEIPASS # pylint: disable=no-member
else:
    # running normally
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Getting our connection strings, both for mongo and redis
load_dotenv()
connection_string_mongo = os.environ['MY_CONNECTION_STRING_MONGO']
connection_string_redis = os.environ['MY_CONNECTION_STRING_REDIS']


app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = '%s' % connection_string_redis
# app.config['CELERY_RESULT_BACKEND'] = '%s' % connection_string_redis

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)




# Any additional configuration options for Celery can be passed directly from Flask's configuration through the celery.conf.update() call. 
# The CELERY_RESULT_BACKEND option is only necessary if you need to have Celery store status and results from tasks. This application does not require this functionality, but the second does, so it's best to have it configured from the start.

# # This is how the output data looks
# {
#     'msisdn': '5511982420608', 'to': '5511950110187',
#     'messageId': '16000002C9BF8495', 'text': 'Test today',
#     'type': 'text', 'keyword': 'TEST', 'api-key': '4f03c64b',
#     'message-timestamp': '2020-09-28 21:20:21'
# }


@app.route("/webhooks/inbound-message", methods=['GET', 'POST'])
def inbound_message():
    # global data
    # data = request.get_json()
    # pprint(data)
    # print('This is the json response: ' + data)
    # print("Hello Cyber Overlord!")
    # return "200"
    
    if request.is_json:
        print('Using first')
        # pprint('Using pprint:', request.get_json())
        data = request.get_json()
        print('Using print:', data)
        # Then invoke our long running background task
        print('Invoking our long running background task')
        my_async_background_task.delay(data)
        return "200"
    
    else:
        print('Using second')
        data = dict(request.form) or dict(request.args)
        # pprint('Using pprint:', data)
        print('Using print:', data)

        # Then invoke our long running background task
        print('Invoking our long running background task')
        my_async_background_task.delay(data)
        return "200"
    
    return ('', 204)


@app.route("/webhooks/inbound-status", methods=['GET', 'POST'])
def inbound_status():
    # data = request.get_json()
    # pprint(data)
    # print(data)
    return "200"


# Any functions that you want to run as background tasks need to be decorated with the celery.task
@celery.task
def my_async_background_task(data):
    try:
        # # # ******************************************************************************************************
        # # Testing One
        # print('I will be sleeping for the next 1min...')
        # time.sleep(60)
        # print('I am done sleeping!')

        # # # ******************************************************************************************************
        # Use cases
        # data = {
        # 'msisdn': '5511982420608', 'to': '5511950110187', 'messageId': '16000002C9BF8495',
        # 'text': 'Test today', 'type': 'text', 'keyword': 'TEST', 'api-key': '4f03c64b', 'message-timestamp': '2020-09-28 21:20:21'
        # }

        # # Setting our data
        # data = data
        print(data)

        sender_mobile = data['msisdn']
        destination_mobile = data['to']
        messageId = data['messageId']
        message_body = data['text']
        timestamp = data['message-timestamp']

        # # ******************************************************************************************************
        # # Confirmations
        # print(sender_mobile)
        # print(destination_mobile)
        # print(messageId)
        # print(message_body)
        # print(timestamp)

        # # ******************************************************************************************************
        # Automatically replying to the message
        client = nexmo.Client(key='4f03c64b', secret='IEic08RSYc21NwMb')
        # Send message
        client.send_message({
            'from': 'Digital T Company',
            'to': sender_mobile,
            'text': f'Hello customer- {sender_mobile}, you have been added to the list...stay tuned for further instructions.. Thank you.'
        })

        # Confirmation for message sent.
        print('Message sent successfully!!')


        # # # ******************************************************************************************************
        # Connecting to a Database in Cloud.(UPLOADING CODES TO DATABASE FOR REFERENCE PURPOSES)
        # This is a python script to illustrate or show how pymongo is used to interact with mongoDB
        #Mongo Database is a "Non SQL" Database.

        # ********************************************************************************************************************
        # Database collection --> comprising of document/records(record11, record2, record3....recordn) from clients.
        # Hence the following chain = Database--->Collection--->Document/Records
        # ********************************************************************************************************************

        # Connection to the default host and port.
        # client = MongoClient()
        # Or we can also specify the host and port explicitly as follows.
        # client = MongoClient('localhost', 27017)

        client = MongoClient('%s' % connection_string_mongo)

        time.sleep(3)
        print("Database connected!!")

        # Getting or creating(If not already present), a database called digitalpro_database
        db = client.digitalpro_database

        # Getting or creating(If not already present), a collection(Named activationcodes_collection)
        # inside the digitalpro_database database
        collection = db.digitalpro_collection

        # ********************************************************************
        # INSERT OPERATION                        ----> C
        # The document here is 'record1'
        # Creating a new document/record named record1.

        record1 = {
            "MSISDN": sender_mobile,
            "DESTINATION PHONE": destination_mobile,
            "MESSAGE ID": messageId,
            "MESSAGE BODY": message_body,
            "TIMESTAMP": timestamp,
            "date": datetime.datetime.utcnow()
        }

        #Inserting document/record into the collection.
        collection.insert_one(record1)

        # Print confirmation message
        print("Database operation successful!!")

        # close our connection and free up resources
        client.close()

    except Exception as e:
        print(e)
        pass

    return







# if __name__ == '__main__':
#     app.run(port=3000)


if __name__ == '__main__':
    app.run(host='0.0.0.0')