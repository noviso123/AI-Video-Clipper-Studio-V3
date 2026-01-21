import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

PROJECT_FOLDER_NAME = 'AI-Video-Clipper-Studio-V3'
FILES_TO_UPDATE = [
    'colab_requirements.txt',
    'debug_imports.py'
]

def get_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token inválido ou expirado. Rode o setup de auth novamente.")

    return build('drive', 'v3', credentials=creds)

def find_folder(service, name):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        return None
    return files[0]['id']

def upload_file(service, filepath, parent_id):
    filename = os.path.basename(filepath)
    print(f"⬆️  Enviando: {filename}")

    # Check exist
    query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])

    media = MediaFileUpload(filepath, resumable=True)

    if files:
        file_id = files[0]['id']
        service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id'
        ).execute()
        print(f"   ✅ Atualizado (ID: {file_id})")
    else:
        file_metadata = {
            'name': filename,
            'parents': [parent_id]
        }
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print("   ✅ Criado novo")

def main():
    print("🚀 Iniciando Hotfix Upload...")
    try:
        service = get_drive_service()
        folder_id = find_folder(service, PROJECT_FOLDER_NAME)

        if not folder_id:
            print(f"❌ Erro Crítico: Pasta '{PROJECT_FOLDER_NAME}' não encontrada no Drive.")
            return

        print(f"📂 Pasta encontrada: {folder_id}")

        for fname in FILES_TO_UPDATE:
            if os.path.exists(fname):
                upload_file(service, fname, folder_id)
            else:
                print(f"⚠️ Arquivo local não encontrado: {fname}")

        print("\n✅ Hotfix aplicado com sucesso!")

    except Exception as e:
        print(f"❌ Falha: {e}")

if __name__ == "__main__":
    main()
