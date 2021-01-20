# Working with flask, celery and Nexmo
import time, bson, json, os, sys, datetime, string, random
from bson import ObjectId
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import dns

from flask import Flask, request, jsonify
from celery import Celery
from celery.schedules import crontab
import nexmo

import pandas as pd
import numpy as np
import gspread
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials



# import sys, os, time
# Accessing files in directories
if getattr(sys, 'frozen', False):
    # running in a bundled form
    base_dir = sys._MEIPASS # pylint: disable=no-member
else:
    # running normally
    base_dir = os.path.dirname(os.path.abspath(__file__))


# Getting our connection strings, both for mongo and redis and other enviroment variables
load_dotenv()

connection_string_mongo = os.environ['MY_CONNECTION_STRING_MONGO']
connection_string_redis = os.environ['MY_CONNECTION_STRING_REDIS']

nexmo_api_key = os.environ['NEXMO_API_KEY']
nexmo_api_secret = os.environ['NEXMO_API_SECRET']

sheet_key = os.environ["ATHENAHEALTHGSHEET_KEY"]
athena_private_key_id = os.environ["ATHENA_PRIVATE_KEY_ID"]
athena_private_key = os.environ["ATHENA_PRIVATE_KEY"]


app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = '%s' % connection_string_redis
# app.config['CELERY_RESULT_BACKEND'] = '%s' % connection_string_redis

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Disable UTC so that Celery can use local time
# celery.conf.enable_utc = False

# Enable UTC 
celery.conf.enable_utc = True


# Any additional configuration options for Celery can be passed directly from Flask's configuration through the celery.conf.update() call. 
# The CELERY_RESULT_BACKEND option is only necessary if you need to have Celery store status and results from tasks. This application does not require this functionality, but the second does, so it's best to have it configured from the start.


@app.route("/index", methods=['GET', 'POST'])
def inbound_message():
    print('Welcome to the Athena Health Cloud application...')
    return "Welcome to the Athena Health Cloud application... 200 OK"








# Any functions that you want to run as background tasks need to be decorated with the celery.task
@celery.task
def our_celery_task():
    try:
        print('Running scheduled app...')
        # Collect our data from googlesheet in the cloud and convert to pandas df
        # Operation between pandasDataframe and Googlesheet

        scope = ['https://spreadsheets.google.com/feeds']

        # get our our json credentials
        credentials_file_dict = {
                                "type": "service_account",
                                "project_id": "athenahealth-project1",
                                "private_key_id": "%s" % athena_private_key_id,
                                "private_key": "%s" % athena_private_key,
                                "client_email": "athenahealth-serviceid1@athenahealth-project1.iam.gserviceaccount.com",
                                "client_id": "115930973993933157841",
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/athenahealth-serviceid1%40athenahealth-project1.iam.gserviceaccount.com"
                                }

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_file_dict, scope)

        gc = gspread.authorize(credentials)
        work_sheet = gc.open_by_key("%s" % sheet_key)   # the spreadsheet-key-here
        sheet = work_sheet.sheet1

        df =  pd.DataFrame(sheet.get_all_records())
        # Darn! the column names are messy (need fix!)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
        # # confirmation1 
        # print(df.head())


        # extract our Athena health data into this list
        # # This is how the output data of the googlesheet looks like
        client_name_list = []
        client_dob_list = []
        client_phone_no_list = []

        for clientIdentifier in df.itertuples():
            if clientIdentifier.name == "":
                break
            client_name = clientIdentifier.name
            client_dob = clientIdentifier.date_of_birth
            client_phone_no = clientIdentifier.phone_number

            client_name_list.append(client_name)
            client_dob_list.append(client_dob)
            client_phone_no_list.append(client_phone_no)

        # # Confirmation2
        # print('\n')
        # for client_name, client_dob, client_phone_no in zip(client_name_list, client_dob_list, client_phone_no_list):
        #     print(f"Client's name is: {client_name}, date of birth is: {client_dob} and phone number is: {client_phone_no}")

        print('\n')
        print("All data loaded from googlesheet successfully!...please wait..")
        print("The other parts of the automation process should begin any moment from now..")
        client = nexmo.Client(key='%s' % nexmo_api_key, secret='%s' % nexmo_api_secret)  # API Connections credentials

        message_send_count = 1
        for client_name, client_dob, client_phone_no in zip(client_name_list, client_dob_list, client_phone_no_list):
            try:
                print(f"Client's name is: {client_name}, date of birth is: {client_dob} and phone number is: {client_phone_no}")
                # # # ****************************************************************************************************
                # # ******************************************************************************************************
                # # ******************************************************************************************************
                # Automatically replying to the message
                # Send message
                client.send_message({
                    'from': 'Athena Health Company',
                    'to': client_phone_no,
                    'text': f'Hello {client_name}!, your personal data are -- name: {client_name}, date of birth: {client_dob} and phone number: {client_phone_no}. You are receiving this sms as an automated message to verify your personal details, thank you.'
                })

                # Confirmation for message sent.
                print(f'Message {message_send_count} sent successfully!!')


                # # # # ******************************************************************************************************
                # # Connecting to a Database in Cloud.(UPLOADING CODES TO DATABASE FOR REFERENCE PURPOSES)
                # # This is a python script to illustrate or show how pymongo is used to interact with mongoDB
                # #Mongo Database is a "Non SQL" Database.

                # # ********************************************************************************************************************
                # # Database collection --> comprising of document/records(record11, record2, record3....recordn) from clients.
                # # Hence the following chain = Database--->Collection--->Document/Records
                # # ********************************************************************************************************************

                # # Connection to the default host and port.
                # # client = MongoClient()
                # # Or we can also specify the host and port explicitly as follows.
                # # client = MongoClient('localhost', 27017)

                # client = MongoClient('%s' % connection_string_mongo)

                # time.sleep(3)
                # print("Database connected!!")

                # # Getting or creating(If not already present), a database called digitalpro_database
                # db = client.digitalpro_database

                # # Getting or creating(If not already present), a collection(Named activationcodes_collection)
                # # inside the digitalpro_database database
                # collection = db.digitalpro_collection

                # # ********************************************************************
                # # INSERT OPERATION                        ----> C
                # # The document here is 'record1'
                # # Creating a new document/record named record1.

                # record1 = {
                #     "MSISDN": sender_mobile,
                #     "DESTINATION PHONE": destination_mobile,
                #     "MESSAGE ID": messageId,
                #     "MESSAGE BODY": message_body,
                #     "TIMESTAMP": timestamp,
                #     "date": datetime.datetime.utcnow()
                # }

                # #Inserting document/record into the collection.
                # collection.insert_one(record1)

                # # Print confirmation message
                # print("Database operation successful!!")

                # # close our connection and free up resources
                # client.close()

            except:
                pass

            finally:
                # Increment message receipt count
                message_send_count += 1

    except Exception as e:
        print(e)
        pass

    finally:
        # Reset all data list
        client_name_list = []
        client_dob_list = []
        client_phone_no_list = []

    return






# Then add our_celery_task function to the beat schedule
celery.conf.beat_schedule = {
    "first-celery-task": {
        "task": "app.our_celery_task",
        "schedule": crontab(minute="*/3")   # configured to run at every 3mins
    }
}


# Then use this command to run the beat scheduler fo the app above using the following command
# celery -A app.celery worker -B --loglevel=INFO







































# if __name__ == '__main__':
#     app.run(port=3000)


if __name__ == '__main__':
    app.run(host='0.0.0.0')