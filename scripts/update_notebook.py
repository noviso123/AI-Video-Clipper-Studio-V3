import json

notebook_path = "OpenInApp_Colab.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Encontrar a célula de instalação (Cell index 2, based on previous view)
# Confirming source contains "!pip install -r colab_requirements.txt"
target_cell = None
for cell in nb["cells"]:
    if "source" in cell:
        source_text = "".join(cell["source"])
        if "Instalação Otimizada" in source_text:
            target_cell = cell
            break

if target_cell:
    print("✅ Célula de instalação encontrada.")
    new_commands = [
        "\n",
        "print(\"🧠 Instalando e Iniciando Ollama...\")\n",
        "!curl -fsSL https://ollama.com/install.sh | sh\n",
        "import subprocess\n",
        "import time\n",
        "\n",
        "# Iniciar Ollama em background\n",
        "subprocess.Popen([\"ollama\", \"serve\"])\n",
        "time.sleep(5) # Esperar servidor subir\n",
        "\n",
        "print(\"📥 Baixando modelo Llama3 (pode demorar um pouco)...t\")\n",
        "!ollama pull llama3\n",
        "print(\"✅ Ollama Pronto!\")\n"
    ]

    # Append to source
    target_cell["source"].extend(new_commands)

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=4)
    print("✅ Notebook atualizado com sucesso!")
else:
    print("❌ Célula não encontrada!")
