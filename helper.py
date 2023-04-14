

import datetime
import re
import json
import boto3
from secretManager import AWSSecret
import logging
from botocore.exceptions import ClientError
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from datetime import timedelta, date
import base64
import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from language import translate_dict

##### VALIDATIONS #####

def validateEmail(email):
    pat = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if re.match(pat,email) and (len(email)>0):
        return True
    return False

def validateParticipants(participants):
    if len(participants)>0:
        someEmailNotValid=False
        for email in participants:
            if validateEmail(email) is False:
                someEmailNotValid=True
        
        if (someEmailNotValid):       
            return False
        else:
            return True
    else:
        return True
       
def is_not_empty(s):
    if s is None:
        return False
    else:
        return bool(s and s.strip())    
    

###### DATE LIMIT ACCORDING TWO DAYS FOR PROCESSING #####

def get_limit_date(date):
    day_of_week_in_two_days = (date + timedelta(days=2)).weekday()
    if (date.weekday()==5): ## today is saturday
        return (date + timedelta(days=3))
    else:
        if (date.weekday()==6): ## today is sunday
            return (date + timedelta(days=2))
        else:
            if day_of_week_in_two_days in (5,6):
                return (date + timedelta(days=4))
            else:
                return (date+ timedelta(days=2))

###### UPLOAD FILE TO S3 #######

def upload_file_to_bucket(file, bucket, name ):
    secrets = json.loads(AWSSecret().get_secret(secret_name="prod/app/pedidosproc", region_name="us-east-1"))
    s3 = boto3.client(
        service_name="s3",
        region_name="us-east-1",
        aws_access_key_id=secrets["keyid"],
        aws_secret_access_key=secrets["secretkey"],
    )
    try:
        s3.upload_fileobj(file, bucket, name,ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        logging.error(e)
        return False
    
    return f"https://{bucket}.s3.amazonaws.com/{name}"

##### TRANSLATIONS #####

def traslate(string, language):

    try:
        return translate_dict[string][language]
    except:
        return "Unknown"

##### CREATE GRID FOR FIELDS/CROPS AND MONITORS #####

def createGrid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)
    if not df.empty:
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)

    gb.configure_pagination(enabled=True)
    my_gridOptions = gb.build()

    new_dataframe = AgGrid(df,
                    gridOptions = my_gridOptions,
                    reload_data=False,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    enable_enterprise_modules=False
    )
    return new_dataframe

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def get_private_key() -> str:
    secret = get_secret("prod/crypt/rsa","us-west-2")
    raw_private_key = secret['api_private_rsa_4096']
    pem_private_key = "-----BEGIN RSA PRIVATE KEY-----\n{0}\n-----END RSA PRIVATE KEY-----".format(raw_private_key)
    return pem_private_key

def decrypt_token(token_string: str) -> dict:
    pem_private_key = get_private_key()

    private_key = serialization.load_pem_private_key(
        pem_private_key.encode(),
        password=None,
        backend=default_backend()
    )
    decrypted = private_key.decrypt(
        base64.urlsafe_b64decode(token_string + '=' * (4-len(token_string)%4)),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return json.loads(str(decrypted, 'utf-8'))