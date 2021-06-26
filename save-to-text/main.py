# [START functions_ocr_setup]
import base64
import json
import os
import re

from google.cloud import pubsub_v1
from google.cloud import storage

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()

# [Make sure to initiate the GCP Project ID on varible environtment before deploying the functions]
project_id = os.environ["GCP_PROJECT"]
# [END functions_ocr_setup]


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


# [START functions_ocr_save]
def save_result(event, context):
    if event.get("data"):
        message_data = base64.b64decode(event["data"]).decode("utf-8")
        message = json.loads(message_data)
    else:
        raise ValueError("Data sector is missing in the Pub/Sub message.")

    text = validate_message(message, "text")
    filename = validate_message(message, "filename")

    print("Received request to save file {}.".format(filename))

    # [Make sure to initiate the Result bucket on varible environtment before deploying the functions]
    bucket_name = os.environ["RESULT_BUCKET"]
    result_filename = "{}.txt".format(filename)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(result_filename)

    regex = "\d{16}"
    list_nik = re.findall(regex,text)
    num = len(list_nik)
    # [To determine whether it is has a single ID on the document or multiple ID]
    if num == 1 :
        nik = list_nik[0]
        print("Single NIK found : {}".format(nik))
    else:
        nik_text = ["NIK_IBU", "NIK_AYAH", "NIK_PELAPOR", "NIK_SAKSI_1", "NIK_SAKSI_2"]
        dict_nik = dict(zip(nik_text,list_nik))
        nik = json.dumps(dict_nik)
        print("Multiple NIK found : {}".format(nik))

    print("Saving result to {} in bucket {}.".format(result_filename, bucket_name))
    blob.upload_from_string(nik)

    print("File saved.")


# [END functions_ocr_save]
