import json
import boto3
import shutil
import os
import os.path
from monday import MondayClient
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from botocore.exceptions import ClientError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

''' al enviar informe y cambiar estado a informe enviado desde la columna "estado" de la tabla informe enviado, se desencadenara 
y se subiran los archivos al drive de manera ordenada y en sus respectivas carpetas.
'''

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
SCOPES = ["https://www.googleapis.com/auth/drive"]
DISCOVERY_DOC = "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"
monday_api_key = get_secret()["monday_api"]
mon = MondayClient(monday_api_key)

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credential.json', SCOPES)
        creds = flow.run_local_server(port=0)
    shutil.copyfile('token.json','/tmp/token.json')
    # Save the credentials for the next run
    with open('/tmp/token.json', 'w') as token:
        token.write(creds.to_json())

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

    # Crear el objeto de servicio de la API de Google Drive
    service = build('drive', 'v3', credentials=creds)
    
    
    id_PADRE='1E-nU0ZiWrxqfUYSSkADFPst6hYGQQz8c'
    # Especificar el nombre de la carpeta que se va a buscar
    nombre_carpeta = evento['pulseName']

    # Crear la query para buscar la carpeta por su nombre
    query = "mimeType='application/vnd.google-apps.folder' and trashed=false and name='{}'".format(nombre_carpeta)

    # Realizar la búsqueda de la carpeta
    resultados = service.files().list(q=query, fields='files(id, name)').execute()
    
    # Obtener el ID y nombre de la carpeta encontrada, si hay resultados
    if resultados.get('files', []):
        carpeta = resultados['files'][0]
        id_carpeta = carpeta['id']
        nombre_carpeta = carpeta['name']
        print("La carpeta '{}' fue encontrada con ID: {}".format(nombre_carpeta, id_carpeta))
    else:
        print("No se encontró la carpeta '{}'".format(nombre_carpeta))
        exit()
    
    
    curso=None

    fila=mon.items.fetch_items_by_id(evento['pulseId'])
    for elemento in fila['data']['items'][0]['column_values']:
        if elemento['id']=='reflejo2':
            curso=elemento['text']
            break
    if not curso:
        print('No existe Curso')
        exit()
    
    
    
    # # Especificar el nombre del archivo que se va a buscar
    # nombre_archivo='Asistencia '+curso
    
    # # Crear la query para buscar el archivo por su nombre
    # query = "trashed=false and name='{}'".format(nombre_archivo)
    
    # # Realizar la búsqueda del archivo
    # resultados = service.files().list(q=query, fields='files(id, name)').execute()
    
    # # Obtener el ID y nombre del archivo encontrado, si hay resultados
    # if resultados.get('files', []):
    #     archivo = resultados['files'][0]
    #     id_archivo = archivo['id']
    #     nombre_archivo = archivo['name']
    #     print("El archivo '{}' fue encontrado con ID: {}".format(nombre_archivo, id_archivo))
    #     exit()
    # else:
    #     print("No se encontró el archivo '{}'".format(nombre_archivo))
