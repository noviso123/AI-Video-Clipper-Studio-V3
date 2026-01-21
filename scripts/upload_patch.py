import os
import pickle
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Config
TOKEN_FILE = 'token.pickle'
PROJECT_NAME = 'AI-Video-Clipper-Studio-V3'

def get_service():
    if not os.path.exists(TOKEN_FILE):
        print("❌ Token não encontrado. Rode o upload completo primeiro.")
        return None
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    return build('drive', 'v3', credentials=creds)

def find_folder(service, name, parent_id=None):
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields='files(id)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def upload_file(service, file_path, parent_id):
    print(f"⬆️  Subindo: {file_path.name}")
    file_metadata = {'name': file_path.name, 'parents': [parent_id]}
    media = MediaFileUpload(str(file_path), resumable=True)
    # Check if exists to update or delete/recreate? Just create (Drive allowsdupes but usually confusing)
    # Let's delete existing with same name to avoid clutter
    query = f"name='{file_path.name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id)').execute()
    for f in results.get('files', []):
        service.files().delete(fileId=f['id']).execute()
        print(f"   ♻️  Versão antiga removida.")

    service.files().create(body=file_metadata, media_body=media).execute()
    print("   ✅ OK")

def main():
    service = get_service()
    if not service: return

    print("🔍 Localizando projeto no Drive...")
    root_id = find_folder(service, PROJECT_NAME)
    if not root_id:
        print(f"❌ Pasta '{PROJECT_NAME}' não encontrada no Drive.")
        return

    # 1. Upload do ZIP atualizado (Raiz)
    zip_path = Path("AI_Video_Clipper_V3_Ultimate.zip")
    if zip_path.exists():
        upload_file(service, zip_path, root_id)

    # 2. Upload da Fonte (src/assets/fonts)
    # Encontrar/Criar caminho
    current_id = root_id
    for folder in ['src', 'assets', 'fonts']:
        next_id = find_folder(service, folder, current_id)
        if not next_id:
            print(f"📁 Criando pasta: {folder}")
            meta = {'name': folder, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [current_id]}
            next_id = service.files().create(body=meta).execute()['id']
        current_id = next_id

    # Upload da fonte
    font_path = Path("src/assets/fonts/Anton-Regular.ttf")
    if font_path.exists():
         upload_file(service, font_path, current_id)

    print("\n✅ Patch de atualização concluído!")

if __name__ == "__main__":
    main()
