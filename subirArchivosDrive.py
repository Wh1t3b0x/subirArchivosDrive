import json
import boto3
from monday import MondayClient
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "Monday_API"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see

        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        raise e

    # Decrypts secret using the associated KMS key.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    return json.loads(get_secret_value_response["SecretString"])


# se asigna la key y los ids necesarios
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
monday_api_key = get_secret()["monday_api"]
mon = MondayClient(monday_api_key)
column_id = {"reflejo70", "archivo6", "archivo4", "archivo20", "dup__of_orden_de_compra", "archivo2", "archivo1"}
#reflejo70 = bases, archivo6 = sin ingresos, archivo4 = programa, archivo20 = CSV notas
# dup__of_orden_de_compra = informe, archivo2 = diplomas, archivo1 = carta de recomendacion

def syncchallenge(event: dict):
    try:
        event_body = json.loads(event["body"])
        challenge = {"challenge": event_body["challenge"]}
        return challenge
    except Exception as e:
        return


def lambda_handler(event, context):
    # if challenge := syncchallenge(event):
    #     return {
    #         "isBase64Encoded": False,
    #         "statusCode": 200,
    #         "body": json.dumps(challenge),
    #         "headers": {"content-type": "application/json"},
    #     }
    
    evento = json.loads(event["body"])["event"]

    pulso_id = evento["pulseId"]
    columnas = mon.items.fetch_items_by_id(pulso_id)["data"]["items"][0]["column_values"]
    print (columnas)

    bases = None
    sinIngresos = None
    programa = None
    csvNotas = None
    informe = None
    diplomas = None
    cartaRecomendacion = None

    for columna in columnas:
        if columna["id"] == "reflejo70":
            bases = columna["url"]
            print(bases)

    for columna in columnas:
        if columna["id"] == "archivo6":
            sinIngresos = columna["url"]
            print(sinIngresos)

    for columna in columnas:
        if columna["id"] == "archivo4":
            programa = columna["url"]
            print(programa)
    
    for columna in columnas:
        if columna["id"] == "archivo20":
            csvNotas = columna["url"]
            print(csvNotas)
    
    for columna in columnas:
        if columna["id"] == "dup__of_orden_de_compra":
            informe = columna["url"]
            print(informe)
    
    for columna in columnas:
        if columna["id"] == "archivo2":
            diplomas = columna["url"]
            print(diplomas)
    
    for columna in columnas:
        if columna["id"] == "archivo1":
            cartaRecomendacion = columna["url"]
            print(cartaRecomendacion)