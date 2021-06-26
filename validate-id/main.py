import os
import json
import re

from io import StringIO
from google.cloud import pubsub_v1
from google.cloud import storage

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()

project_id = os.environ["GCP_PROJECT"]
topic_name = 'email_notification'

# [START message_validatation_helper]
def validate_message(message, param):
    var = message.get(param)
    if not var:
        raise ValueError(
            "{} is not provided. Make sure you have \
                          property {} in the request".format(
                param, param
            )
        )
    return var


# [END message_validatation_helper]

# [START functions_ocr_process]
def process_file(file, context):
    bucket = validate_message(file, "bucket")
    name = validate_message(file, "name")
    
    list_blobs(bucket,name)

    print("File {} processed.".format(file["name"]))


# [END functions_ocr_process]

def list_blobs(bucket_name,name):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    # Looking through bucket to find the same document ID
    id_file = name[0:6]
    filenames_list = []
    for blob in blobs:
         print(blob.name)
         match_file_name = bool(re.match(id_file,blob.name))
         if match_file_name == True:
             filenames_list.append(blob.name)
    #end of looping

    regex_nik = "\d{16}"

    if len(filenames_list)==1:
        print("No match document found")
    else:
        print("Multiple document found")

        bucket = storage_client.get_bucket(bucket_name)
        
        for i in range(len(filenames_list)):
            blob = bucket.blob(filenames_list[i])
            blob = blob.download_as_string()
            blob = blob.decode('utf-8')

            print("Success get the nik : {}".format(blob))

            long_text = len(blob)
            if long_text == 16:
                single_nik = str(blob)
            else:
                multi_nik = json.loads(blob)
            
        multi_nik_value = multi_nik.values()
        
        if single_nik in multi_nik_value:
            document_status = "The document is verified. Please do follow this instruction below to continue."
        else:
            document_status = "The document is unverified. Please do follow this instruction below to continue."
        print(document_status)
        
        message = {
            "text": document_status,
        }
        message_data = json.dumps(message).encode("utf-8")
        topic_path = publisher.topic_path(project_id, topic_name)
        future = publisher.publish(topic_path, data=message_data)
        future.result()