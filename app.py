from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import subprocess
import os
import sys
import threading
import time
import queue
import json # Added for metadata reading

from src.core.state_manager import StateManager

app = Flask(__name__)
CORS(app)

# Config
# Detectar executável Python de forma compatível
if sys.platform == "win32":
    PYTHON_EXE = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(PYTHON_EXE):
        PYTHON_EXE = sys.executable # Fallback para o python atual
else:
    PYTHON_EXE = os.path.join(os.getcwd(), 'venv', 'bin', 'python')
    if not os.path.exists(PYTHON_EXE):
        PYTHON_EXE = sys.executable
SCRIPT_PATH = os.path.join(os.getcwd(), 'main.py')

# Global State
global_process = None
state_manager = StateManager()
process_lock = threading.Lock()

def monitor_process(proc):
    """Lê stdout do processo e salva no state manager"""
    global global_process
    try:
        # Ler linha a linha
        for line in iter(proc.stdout.readline, ''):
            if not line: break
            state_manager.add_log(line.strip())

        proc.stdout.close()
        return_code = proc.wait()

        if return_code == 0:
            state_manager.add_log("✅ [PROCESS FINISHED] Sucesso!")
            state_manager.update_status("done")
        else:
            state_manager.add_log(f"⚠️ [PROCESS FINISHED] Exit Code: {return_code}")
            state_manager.update_status("error")

    except Exception as e:
        state_manager.add_log(f"[ERROR] Monitor thread crashed: {str(e)}")
        state_manager.update_status("error")
    finally:
        with process_lock:
            global_process = None

# --- ERROR HANDLERS ---
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"status": "error", "message": str(e), "code": 500}), 200

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"status": "error", "message": "Endpoint não encontrado", "code": 404}), 200

@app.route('/browse')
def browse_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo de vídeo",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*.*")]
        )
        root.destroy()
        return jsonify({"status": "success", "path": file_path if file_path else ""}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Limpa arquivos temporários para reprocessamento do zero"""
    import shutil

    temp_dir = os.path.join(os.getcwd(), 'temp')
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            try:
                path = os.path.join(temp_dir, f)
                if os.path.isfile(path):
                    os.remove(path)
            except Exception as e:
                print(f"Erro ao deletar {f}: {e}")

    # Atualizar estado
    state_manager.state["logs"] = []
    state_manager.state["status"] = "idle"
    state_manager.save_state()

    return jsonify({"status": "ok", "message": "Cache limpo com sucesso"})

@app.route('/exports/<path:filename>')
def serve_exports(filename):
    from flask import send_from_directory
    exports_dir = os.path.join(os.getcwd(), 'exports')
    return send_from_directory(exports_dir, filename)


@app.route('/api/clips')
def list_clips():
    """Lista os clipes gerados na pasta exports agrupados"""
    exports_dir = os.path.join(os.getcwd(), 'exports')
    if not os.path.exists(exports_dir):
        return jsonify([])

    # Agrupar arquivos por ID (ex: clip_01)
    clips = {}

    for f in os.listdir(exports_dir):
        # Ex: clip_01_score85.mp4
        if f.startswith('clip_') and f.endswith('.mp4'):
            parts = f.split('_') # ['clip', '01', 'score85.mp4']
            if len(parts) >= 2:
                idx = parts[1]
                if idx not in clips: clips[idx] = {}
                clips[idx]['video'] = f
                # Tentar extrair score
                if 'score' in f:
                    try:
                        score_part = f.split('score')[1].replace('.mp4', '')
                        clips[idx]['score'] = int(score_part)
                    except:
                        clips[idx]['score'] = 0

        # Ex: thumb_01.jpg
        elif f.startswith('thumb_') and f.endswith('.jpg'):
            idx = f.split('_')[1].replace('.jpg', '')
            if idx not in clips: clips[idx] = {}
            clips[idx]['thumb'] = f

        # Ex: metadata_01.json
        elif f.startswith('metadata_') and f.endswith('.json'):
            idx = f.split('_')[1].replace('.json', '')
            if idx not in clips: clips[idx] = {}

            # Ler título do JSON
            try:
                with open(os.path.join(exports_dir, f), 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    clips[idx]['title'] = data.get('viral_titles', ['Sem título'])[0]
            except:
                clips[idx]['title'] = "Erro ao ler metadados"

    # Converter dict para lista ordenada
    results = []
    for idx, data in clips.items():
        if 'video' in data: # Só mostrar se tiver vídeo
            results.append({
                'id': idx,
                'video': data.get('video'),
                'thumb': data.get('thumb', ''),
                'title': data.get('title', f"Clip {idx}"),
                'score': data.get('score', 0)
            })

    # Ordenar por score (maior primeiro)
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results)

@app.route('/status')
def get_status():
    """Retorna estado completo"""
    state = state_manager.get_full_state()
    # Adicionar flag running real-time
    with process_lock:
        state['running'] = global_process is not None
    return jsonify(state)

@app.route('/run', methods=['POST'])
def run_clipper():
    global global_process

    with process_lock:
        if global_process is not None:
            return jsonify({'status': 'error', 'message': 'Já existe um processo em execução.'})

    data = request.json
    mode = data.get('mode')
    input_val = data.get('input')

    # Resetar estado
    state_manager.set_project(input_val, mode)

    cmd = [PYTHON_EXE, SCRIPT_PATH]
    if mode == 'url':
        cmd.extend(['--url', input_val])
    else:
        cmd.extend(['--file', input_val])

    cmd.extend(['--clips', '3', '--captions', '--whisper-model', 'tiny', '--broll', '--variants', '--critic'])

    try:
        # Iniciar processo
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
            cwd=os.getcwd()
        )

        with process_lock:
            global_process = proc

        # Iniciar thread de monitoramento
        t = threading.Thread(target=monitor_process, args=(proc,), daemon=True)
        t.start()

        return jsonify({'status': 'success', 'message': 'Iniciando processamento...'})
    except Exception as e:
        state_manager.update_status("error")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stream')
def stream_logs():
    def generate():
        current_idx = 0
        while True:
            state = state_manager.get_full_state()
            logs = state['logs']
            buffer_len = len(logs)

            with process_lock:
                is_running = global_process is not None

            if current_idx < buffer_len:
                chunk = logs[current_idx:buffer_len]
                for line in chunk:
                    yield f"data: {line}\n\n"
                current_idx = buffer_len

            if not is_running and current_idx >= buffer_len:
                break

            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Servidor rodando em http://127.0.0.1:5000")
    app.run(debug=True, port=5000, threaded=True)
