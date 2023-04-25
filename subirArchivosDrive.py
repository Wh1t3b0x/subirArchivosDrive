import json
import boto3
import re
from monday import MondayClient
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "Monday_API"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see

        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        raise e

    # Decrypts secret using the associated KMS key.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    return json.loads(get_secret_value_response["SecretString"])

#se asigna la key y los ids necesarios
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
monday_api_key = get_secret()["monday_api"]
mon = MondayClient(monday_api_key)
board_id = "3549157032"
column_id = "conectar_tableros60"


def syncchallenge(event: dict):
    try:
        event_body = json.loads(event["body"])
        challenge = {"challenge": event_body["challenge"]}
        return challenge
    except Exception as e:
        return


def lambda_handler(event, context):
    if challenge := syncchallenge(event):
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": json.dumps(challenge),
            "headers": {"content-type": "application/json"},
        }

    evento = json.loads(event["body"])["event"]
    #se toma el id del pulso y el texto en el encargado
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    pulso_id = evento["pulseId"]
    boardId = evento["boardId"]
    columnas = mon.items.fetch_items_by_id(pulso_id)["data"]["items"][0]["column_values"]

    encargado = None
    for columna in columnas:
        if columna["id"] == column_id:
            encargado = columna["text"]
