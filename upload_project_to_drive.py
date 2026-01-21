"""
Script de Upload Automático para Google Drive
Faz upload completo do projeto AI-Video-Clipper-Studio-V3

REQUISITOS:
- pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

COMO USAR:
1. Execute: python upload_project_to_drive.py
2. Na primeira vez, um navegador abrirá para autorização
3. Faça login com sua conta Google
4. O projeto será enviado para: Drive/AI-Video-Clipper-Studio-V3/
"""

import os
import sys
import io
import pickle
from pathlib import Path
from datetime import datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
except ImportError:
    print("❌ Dependências não instaladas!")
    print("Execute: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

class DriveUploader:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Autentica com Google Drive"""
        creds = None

        # Carregar token salvo
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)

        # Se não há credenciais válidas, fazer login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Renovando token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print("❌ Arquivo credentials.json não encontrado!")
                    print("")
                    print("INSTRUÇÕES:")
                    print("1. Acesse: https://console.cloud.google.com/")
                    print("2. Crie um projeto (ou use existente)")
                    print("3. Ative a API do Google Drive")
                    print("4. Crie credenciais OAuth 2.0 (Desktop App)")
                    print("5. Baixe o JSON e salve como 'credentials.json' nesta pasta")
                    print("")
                    sys.exit(1)

                print("🔐 Abrindo navegador para autorização...")
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

            # Salvar token
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            print("✅ Autenticação concluída!")

        self.service = build('drive', 'v3', credentials=creds)

    def create_folder(self, name, parent_id=None):
        """Cria pasta no Drive"""
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = self.service.files().create(
            body=file_metadata,
            fields='id, name'
        ).execute()

        return folder.get('id')

    def find_folder(self, name, parent_id=None):
        """Busca pasta existente"""
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        files = results.get('files', [])
        return files[0]['id'] if files else None

    def upload_file(self, file_path, parent_id=None):
        """Faz upload de um arquivo (Sobrescreve se existir)"""
        file_metadata = {'name': file_path.name}
        if parent_id:
            file_metadata['parents'] = [parent_id]

        # Verificar se arquivo já existe
        query = f"name='{file_path.name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(q=query, fields='files(id)').execute()
        files = results.get('files', [])

        media = MediaFileUpload(str(file_path), resumable=True)

        if files:
            # Atualizar arquivo existente
            file_id = files[0]['id']
            # print(f"   🔄 Atualizando: {file_path.name}")
            file = self.service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
        else:
            # Criar novo arquivo
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

        return file

    def upload_project(self, project_dir):
        """Faz upload do projeto completo"""
        project_dir = Path(project_dir)

        if not project_dir.exists():
            print(f"❌ Diretório não encontrado: {project_dir}")
            return

        print("=" * 60)
        print("📤 UPLOAD DO PROJETO PARA GOOGLE DRIVE")
        print("=" * 60)
        print(f"📁 Projeto: {project_dir.name}")
        print("")

        # Criar/encontrar pasta raiz no Drive
        print("📁 Criando estrutura no Drive...")
        root_folder_id = self.find_folder(project_dir.name)

        if not root_folder_id:
            root_folder_id = self.create_folder(project_dir.name)
            print(f"   ✅ Pasta criada: {project_dir.name}")
        else:
            print(f"   ℹ️  Pasta existente: {project_dir.name}")

        # Arquivos/pastas para ignorar
        ignore = {
            '__pycache__', '.git', '.venv', 'venv',
            'node_modules', '.DS_Store', 'temp'
        }

        # Contadores
        uploaded_files = 0
        uploaded_bytes = 0
        skipped = 0

        # Mapeamento de pastas locais -> IDs no Drive
        folder_map = {project_dir: root_folder_id}

        print("")
        print("📤 Fazendo upload dos arquivos...")
        print("")

        # Percorrer projeto
        for root, dirs, files in os.walk(project_dir):
            # Remover pastas ignoradas
            dirs[:] = [d for d in dirs if d not in ignore]

            current_path = Path(root)

            # Criar subpastas no Drive
            for dir_name in dirs:
                dir_path = current_path / dir_name

                if dir_path in folder_map:
                    continue

                parent_id = folder_map.get(current_path)
                folder_id = self.create_folder(dir_name, parent_id)
                folder_map[dir_path] = folder_id

            # Upload de arquivos
            parent_id = folder_map.get(current_path)

            for filename in files:
                # Pular arquivos ignorados
                if filename.endswith(('.pyc', '.pyo')) or filename in ignore:
                    skipped += 1
                    continue

                file_path = current_path / filename

                try:
                    # Mostrar progresso
                    rel_path = file_path.relative_to(project_dir)
                    print(f"   📄 {rel_path}")

                    # Upload
                    self.upload_file(file_path, parent_id)

                    uploaded_files += 1
                    uploaded_bytes += file_path.stat().st_size

                except Exception as e:
                    print(f"      ⚠️ Erro: {e}")
                    skipped += 1

        # Relatório final
        print("")
        print("=" * 60)
        print("✅ UPLOAD CONCLUÍDO!")
        print("=" * 60)
        print(f"📊 Arquivos enviados: {uploaded_files}")
        print(f"⏭️  Arquivos ignorados: {skipped}")
        print(f"💾 Tamanho total: {uploaded_bytes / (1024*1024):.1f} MB")
        print("")
        print(f"📁 Acesse: https://drive.google.com/drive/my-drive")
        print(f"   Pasta: {project_dir.name}")
        print("=" * 60)

def main():
    # Diretório do projeto
    project_dir = Path(__file__).parent

    print("")
    print("🚀 AI Video Clipper - Upload para Google Drive")
    print("")

    # Criar uploader
    uploader = DriveUploader()

    # Fazer upload
    uploader.upload_project(project_dir)

    print("")
    print("✅ Processo concluído!")
    print("")

if __name__ == "__main__":
    main()
