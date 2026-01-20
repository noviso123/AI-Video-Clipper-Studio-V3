
import os
import sys
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Adjust path to find root files if needed, assuming this runs from root
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Token inválido ou expirado. Execute o upload novamente para re-autenticar.")
            return

    service = build('drive', 'v3', credentials=creds)

    # Search for the folder
    query = "name='AI-Video-Clipper-Studio-V3' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
    files = results.get('files', [])

    if not files:
        print("❌ Pasta 'AI-Video-Clipper-Studio-V3' NÃO encontrada no Drive!")
    else:
        folder = files[0]
        print(f"✅ Pasta Encontrada: {folder['name']}")
        print(f"🔗 Link: {folder['webViewLink']}")
        print(f"🆔 ID: {folder['id']}")

        # List contents
        print("\nConteúdo da pasta:")
        q_files = f"'{folder['id']}' in parents and trashed=false"
        res_files = service.files().list(q=q_files, fields='files(id, name, modifiedTime)').execute()
        items = res_files.get('files', [])

        if not items:
            print("   (Pasta vazia)")
        else:
            print(f"   Total de itens: {len(items)}")
            duplicates = [i for i in items if i['name'] == 'AI_Video_Clipper_Colab.ipynb']
            if duplicates:
                print(f"\\n   ⚠️  Encontradas {len(duplicates)} versões do notebook:")
                for d in duplicates:
                    print(f"      - {d['name']} | ID: {d['id']} | Modificado: {d['modifiedTime']}")
            else:
                 print("   Notebook não encontrado.")

if __name__ == '__main__':
    main()
