import os
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate():
    creds = None
    # Token salvo anteriormente
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Se não houver credenciais válidas, faças login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Procura por credentials.json na raiz
            if not os.path.exists('credentials.json'):
                print("❌ ERRO: Arquivo 'credentials.json' não encontrado!")
                print("1. Vá em https://console.cloud.google.com/apis/credentials")
                print("2. Crie um 'OAuth Client ID' (Desktop App)")
                print("3. Baixe o JSON e salve como 'credentials.json' nesta pasta.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Salvar token para proxima vez
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_folder(service, folder_path, parent_id=None):
    folder_name = os.path.basename(folder_path)

    # Criar pasta no Drive
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    file = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = file.get('id')
    print(f"📁 Criada pasta: {folder_name} ({folder_id})")

    # Upload arquivos
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # Ignorar pastas inúteis
        if item in ['.git', '__pycache__', 'venv', '.venv', 'node_modules', '.env', 'browser_profiles', 'bin', 'exports_v2', 'exports_v3', 'Include', 'Lib', 'obj']:
            continue

        if os.path.isfile(item_path):
            print(f"   ⬆️ Uploading: {item}...")
            file_metadata = {
                'name': item,
                'parents': [folder_id]
            }
            media = MediaFileUpload(item_path, resumable=True)
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        elif os.path.isdir(item_path):
            upload_folder(service, item_path, parent_id=folder_id)

if __name__ == '__main__':
    print("🚀 Iniciando Upload para o Google Drive...")
    service = authenticate()
    if service:
        current_dir = os.getcwd()
        # Upload da pasta atual
        upload_folder(service, current_dir)
        print("\n✅ Upload Concluído!")
