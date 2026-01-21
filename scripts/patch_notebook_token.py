import json
from pathlib import Path

def patch_notebook():
    nb_path = Path("AI_Video_Clipper_Colab.ipynb")

    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    token = "2tvNFAWzP9KMYZGpfCqx1EQmmwN_NPCQKjeqHD7pomCtJFVA"

    # Encontrar a célula do Ngrok
    found = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "ngrok.set_auth_token" in source:
                # Substituir o código
                new_source = [
                    "import os\n",
                    "from pyngrok import ngrok\n",
                    "import subprocess\n",
                    "import time\n",
                    "\n",
                    "# 1. Configurar Ngrok (Token Automático)\n",
                    "print(\"🔑 Configurando Ngrok...\")\n",
                    f"token = \"{token}\"\n",
                    "ngrok.set_auth_token(token)\n",
                    "print(\"✅ Token Ngrok configurado automaticamente!\")\n",
                    "\n",
                    "# 2. Iniciar Flask App em Background\n",
                    "print(\"🚀 Iniciando servidor Flask...\")\n",
                    "flask_process = subprocess.Popen(['python', 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n",
                    "time.sleep(5) # Aguardar inicialização\n",
                    "\n",
                    "# 3. Criar Túnel Público\n",
                    "try:\n",
                    "    # Matar túneis anteriores se houver\n",
                    "    ngrok.kill()\n",
                    "    \n",
                    "    # Criar novo túnel na porta 5005 (Porta do Flask app.py)\n",
                    "    public_url = ngrok.connect(5005)\n",
                    "    print(\"\\n\" + \"=\"*50)\n",
                    "    print(f\"✅ INTERFACE WEB ONLINE!\")\n",
                    "    print(f\"👉 Acesse aqui: {public_url}\")\n",
                    "    print(\"=\"*50 + \"\\n\")\n",
                    "    \n",
                    "    # Manter célula rodando\n",
                    "    print(\"ℹ️  Mantenha esta célula rodando para usar o site.\")\n",
                    "    print(\"ℹ️  Logs do servidor aparecerão abaixo:\")\n",
                    "    \n",
                    "    # Stream logs\n",
                    "    while True:\n",
                    "        line = flask_process.stdout.readline()\n",
                    "        if not line:\n",
                    "            break\n",
                    "        print(line.decode('utf-8').strip())\n",
                    "\n",
                    "except Exception as e:\n",
                    "    print(f\"❌ Erro ao criar túnel: {e}\")\n",
                    "    flask_process.terminate()"
                ]
                cell['source'] = new_source
                found = True
                break

    if found:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=4)
        print("✅ Notebook atualizado com Token Ngrok!")
    else:
        print("❌ Célula do Ngrok não encontrada no Notebook.")

if __name__ == "__main__":
    patch_notebook()
