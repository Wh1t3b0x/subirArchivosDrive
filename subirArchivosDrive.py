import json, boto3, shutil, os, mimetypes, requests
from monday import MondayClient
from botocore.exceptions import ClientError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build


def get_secret():
    secret_name = "Monday_API"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see

        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        raise e

    # Decrypts secret using the associated KMS key.
    return json.loads(get_secret_value_response["SecretString"])
    
BASE_DIR='/tmp/'
MONDAY_API_URL='https://api.monday.com/v2'
SCOPES = ["https://www.googleapis.com/auth/drive"]
DISCOVERY_DOC = "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"
monday_api_key = get_secret()["monday_api"]
mon = MondayClient(monday_api_key)

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credential.json", SCOPES)
        creds = flow.run_local_server(port=0)
    shutil.copyfile("token.json", "/tmp/token.json")
    # Save the credentials for the next run
    with open("/tmp/token.json", "w") as token:
        token.write(creds.to_json())


def obtenerURLPublica(item:dict,id_file):
  assets=item['assets']
  for asset in assets:
    if asset['id']==id_file:
      return asset['public_url']

def get_item_by_id(element_id: str)->dict:
    """
        busca en el elemento con el id element_id, retorna el elemento con sus columnas
    """
    query =f'''{{
        items (ids: {str(element_id)}) {{ id name
            column_values{{ id title text }}
            assets {{ id url name public_url }}  }} }}'''
    data = {'query' : query}
    r = requests.post(url=MONDAY_API_URL, json=data, headers= {"Authorization" : monday_api_key})
    return r.json()["data"]["items"][0]

def syncchallenge(event: dict):
    try:
        event_body = json.loads(event["body"])
        challenge = {"challenge": event_body["challenge"]}
        return challenge
    except Exception as e:
        return


def lambda_handler(event, context):
    evento = json.loads(event["body"])["event"]

    pulso_id = evento["pulseId"]
    columnas = mon.items.fetch_items_by_id(pulso_id)["data"]["items"][0][
        "column_values"
    ]
    # print (columnas)
    
    item=get_item_by_id(pulso_id)
    archivos=[]
    
    datos={}
    for columna in columnas:
        if columna.get('text',None) and 'https://izieduca.monday.com/' in columna['text']:
            archivos.append(columna['text'])
            
    print(archivos)
    
    for archivo in archivos:
        datos[archivo.split('/')[7]]=obtenerURLPublica(item, archivo.split('/')[6])
    print(datos)
    

    # -------------------------------------------------------------------
    # Crear el objeto de servicio de la API de Google Drive
    service = build("drive", "v3", credentials=creds)

    id_PADRE = "1E-nU0ZiWrxqfUYSSkADFPst6hYGQQz8c"
    # Especificar el nombre de la carpeta que se va a buscar
    nombre_carpeta = evento["pulseName"]

    # Crear la query para buscar la carpeta por su nombre
    query = "mimeType='application/vnd.google-apps.folder' and trashed=false and name='{}'".format(
        nombre_carpeta
    )

    # Realizar la búsqueda de la carpeta
    resultados = service.files().list(q=query, fields="files(id, name)").execute()

    # Obtener el ID y nombre de la carpeta encontrada, si hay resultados
    if resultados.get("files", []):
        carpeta = resultados["files"][0]
        id_carpeta = carpeta["id"]
        nombre_carpeta = carpeta["name"]
        print(
            "La carpeta '{}' fue encontrada con ID: {}".format(
                nombre_carpeta, id_carpeta
            )
        )
    else:
        print("No se encontró la carpeta '{}'".format(nombre_carpeta))
        exit()
    
    # Iterar a través de todas las URL de los archivos y subirlos a la carpeta encontrada
    for nombre_archivo, ruta_archivo in datos.items():
        if nombre_archivo.strip() and ruta_archivo.strip():
            # Obtener el tipo de archivo a partir de la ruta del archivo
            tipo_archivo, _ = mimetypes.guess_type(ruta_archivo)

            # Subir el archivo a la carpeta encontrada
            file_metadata = {"name": nombre_archivo, "parents": [id_carpeta]}
            response = requests.get(ruta_archivo)
            open(BASE_DIR+nombre_archivo, "wb").write(response.content)
            media = MediaFileUpload(BASE_DIR+nombre_archivo, mimetype=tipo_archivo)
            archivo = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(
                "Se subió el archivo '{}' con ID: {}".format(
                    nombre_archivo, archivo.get("id")
                )
            )
        else:
            print(
                "El archivo {} no contiene datos y no se cargará.".format(
                    nombre_archivo
                )
            )
