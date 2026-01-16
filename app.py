"""
AI Video Clipper - Backend Flask Server
Complete API for video processing, clip generation, and management
"""
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import subprocess
import os
import sys
import threading
import time
import json
import shutil
from datetime import datetime

from src.core.factory import get_factory
from src.core.state_manager import StateManager
from src.core.config import Config

app = Flask(__name__)
CORS(app, origins="*")

# =====================
# CONFIGURATION
# =====================
BASE_DIR = os.getcwd()
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
SCRIPT_PATH = os.path.join(BASE_DIR, 'main.py')

# Detect Python executable
if sys.platform == "win32":
    PYTHON_EXE = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
else:
    PYTHON_EXE = os.path.join(BASE_DIR, 'venv', 'bin', 'python')
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# =====================
# GLOBAL STATE
# =====================
global_process = None
state_manager = StateManager()
process_lock = threading.Lock()


def monitor_process(proc):
    """Lê stdout do processo e salva no state manager"""
    global global_process
    try:
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
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


# =====================
# ERROR HANDLERS
# =====================
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"status": "error", "message": str(e), "code": 500}), 200


@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"status": "error", "message": "Endpoint não encontrado", "code": 404}), 200


# =====================
# PAGES
# =====================
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


# =====================
# SYSTEM ENDPOINTS
# =====================
@app.route('/api/health')
def health_check():
    """Status completo do sistema"""
    return jsonify({
        "status": "healthy",
        "server": "online",
        "timestamp": datetime.now().isoformat(),
        "apis": {
            "openai": bool(Config.OPENAI_API_KEY),
            "gemini": bool(Config.GEMINI_API_KEY),
            "pexels": bool(Config.PEXELS_API_KEY)
        },
        "local_mode": getattr(Config, 'LOCAL_MODE', True),
        "directories": {
            "temp": os.path.exists(TEMP_DIR),
            "exports": os.path.exists(EXPORTS_DIR)
        },
        "python": PYTHON_EXE,
        "version": "3.0.0"
    })


@app.route('/api/config')
def get_config():
    """Retorna configurações públicas do sistema"""
    return jsonify({
        "whisper_model": getattr(Config, 'WHISPER_MODEL', 'small'),
        "video_fps": getattr(Config, 'VIDEO_FPS', 30),
        "video_width": getattr(Config, 'VIDEO_WIDTH', 1080),
        "video_height": getattr(Config, 'VIDEO_HEIGHT', 1920),
        "clip_duration_min": getattr(Config, 'CLIP_DURATION_MIN', 30),
        "clip_duration_max": getattr(Config, 'CLIP_DURATION_MAX', 60),
        "face_tracking": getattr(Config, 'FACE_TRACKING_ENABLED', True),
        "dynamic_captions": getattr(Config, 'DYNAMIC_CAPTIONS_ENABLED', True),
        "broll_enabled": getattr(Config, 'BROLL_ENABLED', True)
    })


@app.route('/api/system/info')
def system_info():
    """Informações do sistema"""
    import platform

    temp_size = 0
    exports_size = 0

    for f in os.listdir(TEMP_DIR) if os.path.exists(TEMP_DIR) else []:
        path = os.path.join(TEMP_DIR, f)
        if os.path.isfile(path):
            temp_size += os.path.getsize(path)

    for f in os.listdir(EXPORTS_DIR) if os.path.exists(EXPORTS_DIR) else []:
        path = os.path.join(EXPORTS_DIR, f)
        if os.path.isfile(path):
            exports_size += os.path.getsize(path)

    return jsonify({
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "temp_files": len(os.listdir(TEMP_DIR)) if os.path.exists(TEMP_DIR) else 0,
        "temp_size_mb": round(temp_size / (1024 * 1024), 2),
        "exports_files": len(os.listdir(EXPORTS_DIR)) if os.path.exists(EXPORTS_DIR) else 0,
        "exports_size_mb": round(exports_size / (1024 * 1024), 2)
    })


# =====================
# FILE BROWSER
# =====================
@app.route('/browse')
def browse_file():
    """Abre diálogo de seleção de arquivo"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo de vídeo",
            filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"), ("Todos", "*.*")]
        )
        root.destroy()
        return jsonify({"status": "success", "path": file_path or ""})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# =====================
# EXPORTS MANAGEMENT
# =====================
@app.route('/exports/<path:filename>')
def serve_exports(filename):
    """Serve arquivos da pasta exports"""
    return send_from_directory(EXPORTS_DIR, filename)


@app.route('/api/exports/list')
def list_exports():
    """Lista todos os arquivos exportados"""
    if not os.path.exists(EXPORTS_DIR):
        return jsonify({"files": [], "total": 0})

    files = []
    for f in os.listdir(EXPORTS_DIR):
        filepath = os.path.join(EXPORTS_DIR, f)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                "name": f,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": stat.st_mtime,
                "type": f.split('.')[-1] if '.' in f else 'unknown'
            })

    files.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify({"files": files, "total": len(files)})


@app.route('/api/exports/delete/<filename>', methods=['DELETE'])
def delete_export(filename):
    """Deleta arquivo específico"""
    filepath = os.path.join(EXPORTS_DIR, filename)

    if not os.path.realpath(filepath).startswith(os.path.realpath(EXPORTS_DIR)):
        return jsonify({"status": "error", "message": "Acesso negado"}), 403

    if not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "Arquivo não encontrado"}), 404

    try:
        os.remove(filepath)
        return jsonify({"status": "success", "message": f"{filename} deletado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/exports/delete-all', methods=['DELETE'])
def delete_all_exports():
    """Deleta TODOS os exports"""
    deleted_count = 0
    errors = []

    if os.path.exists(EXPORTS_DIR):
        for f in os.listdir(EXPORTS_DIR):
            try:
                path = os.path.join(EXPORTS_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{f}: {str(e)}")

    return jsonify({
        "status": "success",
        "message": f"{deleted_count} arquivos deletados",
        "deleted": deleted_count,
        "errors": errors
    })


@app.route('/api/exports/download/<filename>')
def download_export(filename):
    """Download de arquivo com headers corretos"""
    filepath = os.path.join(EXPORTS_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "Arquivo não encontrado"}), 404

    return send_from_directory(
        EXPORTS_DIR,
        filename,
        as_attachment=True,
        download_name=filename
    )


# =====================
# CLIPS ENDPOINTS
# =====================
@app.route('/api/clips')
def list_clips():
    """Lista clips agrupados com metadados"""
    if not os.path.exists(EXPORTS_DIR):
        return jsonify([])

    clips = {}

    for f in os.listdir(EXPORTS_DIR):
        if f.startswith('clip_') and f.endswith('.mp4'):
            parts = f.split('_')
            if len(parts) >= 2:
                idx = parts[1]
                if idx not in clips:
                    clips[idx] = {}
                clips[idx]['video'] = f

                if 'score' in f:
                    try:
                        score_part = f.split('score')[1].replace('.mp4', '')
                        clips[idx]['score'] = float(score_part)
                    except:
                        clips[idx]['score'] = 0

        elif f.startswith('thumb_') and f.endswith('.jpg'):
            idx = f.split('_')[1].replace('.jpg', '')
            if idx not in clips:
                clips[idx] = {}
            clips[idx]['thumb'] = f

        elif f.startswith('metadata_') and f.endswith('.json'):
            idx = f.split('_')[1].replace('.json', '')
            if idx not in clips:
                clips[idx] = {}
            try:
                with open(os.path.join(EXPORTS_DIR, f), 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    clips[idx]['title'] = data.get('viral_titles', ['Sem título'])[0]
                    clips[idx]['duration'] = data.get('duration', 0)
            except:
                clips[idx]['title'] = "Erro ao ler metadados"

    results = []
    for idx, data in clips.items():
        if 'video' in data:
            results.append({
                'id': idx,
                'video': data.get('video'),
                'thumb': data.get('thumb', ''),
                'title': data.get('title', f"Clip {idx}"),
                'score': data.get('score', 0),
                'duration': data.get('duration', 0)
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results)


@app.route('/api/clips/<clip_id>')
def get_clip(clip_id):
    """Detalhes de um clip específico"""
    video_file = None
    thumb_file = None
    metadata = {}

    for f in os.listdir(EXPORTS_DIR):
        if f.startswith(f'clip_{clip_id}') and f.endswith('.mp4'):
            video_file = f
        elif f == f'thumb_{clip_id}.jpg':
            thumb_file = f
        elif f == f'metadata_{clip_id}.json':
            try:
                with open(os.path.join(EXPORTS_DIR, f), 'r', encoding='utf-8') as jf:
                    metadata = json.load(jf)
            except:
                pass

    if not video_file:
        return jsonify({"status": "error", "message": "Clip não encontrado"}), 404

    return jsonify({
        "id": clip_id,
        "video": video_file,
        "thumb": thumb_file,
        "metadata": metadata
    })


# =====================
# PROCESS CONTROL
# =====================
@app.route('/status')
def get_status():
    """Estado completo do processamento"""
    state = state_manager.get_full_state()
    with process_lock:
        state['running'] = global_process is not None
    state['timestamp'] = datetime.now().isoformat()
    return jsonify(state)


@app.route('/api/generate/autonomous', methods=['POST'])
def generate_autonomous():
    """Geração de conteúdo do zero usando AutonomousFactory"""
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({"status": "error", "message": "URL não fornecida"}), 400

    def run_factory_async():
        with app.app_context():
            try:
                state_manager.clear_logs()
                state_manager.update_status("processing_autonomous")
                state_manager.add_log(f"🧠 INICIANDO CÉREBRO AUTÔNOMO: {url}")

                f = get_factory()
                # O run_factory é síncrono por padrão mas usa result de kickoff
                # Vamos simplificar e rodar direto
                result = f.run(url, is_url=True)

                if "error" in result:
                    state_manager.add_log(f"❌ ERRO: {result['error']}")
                    state_manager.update_status("error")
                else:
                    state_manager.add_log("✨ PROCESSO AUTÔNOMO CONCLUÍDO COM SUCESSO!")
                    state_manager.update_status("done")
            except Exception as e:
                state_manager.add_log(f"❌ ERRO FATAL: {str(e)}")
                state_manager.update_status("error")

    thread = threading.Thread(target=run_factory_async)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "message": "Cérebro autonômo iniciado"})


@app.route('/run', methods=['POST'])
def run_clipper():
    """Inicia processamento de vídeo"""
    global global_process

    with process_lock:
        if global_process is not None:
            return jsonify({'status': 'error', 'message': 'Já existe um processo em execução.'})

    data = request.json
    mode = data.get('mode', 'url')
    input_val = data.get('input', '')

    if not input_val:
        return jsonify({'status': 'error', 'message': 'Input vazio'})

    # Reset state
    state_manager.set_project(input_val, mode)

    # Build command
    cmd = [PYTHON_EXE, SCRIPT_PATH]
    if mode == 'url':
        cmd.extend(['--url', input_val])
    else:
        cmd.extend(['--file', input_val])

    cmd.extend([
        '--clips', str(data.get('clips', 3)),
        '--min-duration', str(data.get('min_duration', 30)),
        '--max-duration', str(data.get('max_duration', 60)),
        '--whisper-model', data.get('whisper_model', 'tiny'),
        '--captions',
        '--broll',
        '--variants',
        '--critic'
    ])

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
            cwd=BASE_DIR
        )

        with process_lock:
            global_process = proc

        t = threading.Thread(target=monitor_process, args=(proc,), daemon=True)
        t.start()

        return jsonify({'status': 'success', 'message': 'Processamento iniciado'})
    except Exception as e:
        state_manager.update_status("error")
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/stop', methods=['POST'])
def force_stop():
    """Para processamento imediatamente"""
    global global_process

    with process_lock:
        if global_process is None:
            return jsonify({"status": "info", "message": "Nenhum processo em execução"})

        try:
            global_process.terminate()
            time.sleep(0.5)
            if global_process and global_process.poll() is None:
                global_process.kill()
            global_process = None

            state_manager.add_log("🛑 [PROCESS STOPPED] Cancelado pelo usuário")
            state_manager.update_status("cancelled")

            return jsonify({"status": "success", "message": "Processo cancelado"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/stream')
def stream_logs():
    """Stream de logs em tempo real via SSE"""
    def generate():
        current_idx = 0
        max_wait = 300  # 5 min timeout
        wait_counter = 0

        while wait_counter < max_wait:
            state = state_manager.get_full_state()
            logs = state['logs']
            buffer_len = len(logs)

            with process_lock:
                is_running = global_process is not None

            if current_idx < buffer_len:
                for line in logs[current_idx:buffer_len]:
                    yield f"data: {line}\n\n"
                current_idx = buffer_len
                wait_counter = 0  # Reset timeout on activity

            if not is_running and current_idx >= buffer_len:
                break

            time.sleep(0.3)
            wait_counter += 1

    return Response(generate(), mimetype='text/event-stream')


# =====================
# CACHE/HISTORY MANAGEMENT
# =====================
@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Limpa cache temporário"""
    deleted = 0
    if os.path.exists(TEMP_DIR):
        for f in os.listdir(TEMP_DIR):
            try:
                path = os.path.join(TEMP_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                deleted += 1
            except:
                pass

    state_manager.state["logs"] = []
    state_manager.state["status"] = "idle"
    state_manager.save_state()

    return jsonify({"status": "success", "message": f"Cache limpo ({deleted} items)"})


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Limpa histórico e estado"""
    state_manager.state = {
        "logs": [],
        "status": "idle",
        "current_project": None,
        "running": False
    }
    state_manager.save_state()

    # Clear temp
    if os.path.exists(TEMP_DIR):
        for f in os.listdir(TEMP_DIR):
            try:
                path = os.path.join(TEMP_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except:
                pass

    return jsonify({"status": "success", "message": "Histórico limpo"})


@app.route('/api/nuke', methods=['DELETE'])
def nuke_everything():
    """APAGA TUDO - exports, temp, logs, estado"""
    global global_process

    # Stop any running process
    with process_lock:
        if global_process:
            try:
                global_process.terminate()
                global_process.kill()
                global_process = None
            except:
                pass

    # Clear state
    state_manager.state = {"logs": [], "status": "idle", "current_project": None, "running": False}
    state_manager.save_state()

    deleted = {"temp": 0, "exports": 0}

    # Clear temp
    if os.path.exists(TEMP_DIR):
        for f in os.listdir(TEMP_DIR):
            try:
                path = os.path.join(TEMP_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                deleted["temp"] += 1
            except:
                pass

    # Clear exports
    if os.path.exists(EXPORTS_DIR):
        for f in os.listdir(EXPORTS_DIR):
            try:
                path = os.path.join(EXPORTS_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                deleted["exports"] += 1
            except:
                pass

    return jsonify({
        "status": "success",
        "message": "TUDO apagado!",
        "deleted": deleted
    })


@app.route('/api/logs')
def get_logs():
    """Retorna apenas os logs"""
    state = state_manager.get_full_state()
    return jsonify({
        "logs": state.get('logs', []),
        "count": len(state.get('logs', []))
    })


@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Limpa apenas os logs"""
    state_manager.state["logs"] = []
    state_manager.save_state()
    return jsonify({"status": "success", "message": "Logs limpos"})


# =====================
# VOICE CLONING (Integrated)
# =====================
VOICE_SAMPLES_DIR = os.path.join(BASE_DIR, 'voice_samples_processed') # Usar processados
if not os.path.exists(VOICE_SAMPLES_DIR):
    VOICE_SAMPLES_DIR = os.path.join(BASE_DIR, 'voice_samples')

VOICE_MODELS_DIR = os.path.join(BASE_DIR, 'models', 'custom_voice_pro')
os.makedirs(VOICE_SAMPLES_DIR, exist_ok=True)
os.makedirs(VOICE_MODELS_DIR, exist_ok=True)


@app.route('/voice-recorder')
def voice_recorder():
    """Página de gravação de voz"""
    return render_template('voice_recorder.html')


@app.route('/voice-test')
def voice_test():
    """Página de teste de voz"""
    return render_template('voice_test.html')


@app.route('/api/voice/upload', methods=['POST'])
def upload_voice_sample():
    """Upload de amostra de voz"""
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo de áudio"}), 400

    audio = request.files['audio']
    sample_id = request.form.get('sample_id', '1')

    # Salvar arquivo
    filename = f"voice_sample_{sample_id}.wav"
    filepath = os.path.join(VOICE_SAMPLES_DIR, filename)
    audio.save(filepath)

    return jsonify({
        "status": "success",
        "message": f"Amostra {sample_id} salva",
        "filename": filename,
        "path": filepath
    })


@app.route('/api/voice/samples')
def list_voice_samples():
    """Lista amostras de voz salvas"""
    samples = []
    if os.path.exists(VOICE_SAMPLES_DIR):
        for f in os.listdir(VOICE_SAMPLES_DIR):
            if f.endswith('.wav'):
                filepath = os.path.join(VOICE_SAMPLES_DIR, f)
                samples.append({
                    "filename": f,
                    "size": os.path.getsize(filepath),
                    "modified": os.path.getmtime(filepath)
                })
    return jsonify({"samples": samples, "count": len(samples)})


@app.route('/api/voice/create-model', methods=['POST'])
def create_voice_model():
    """Cria modelo de voz personalizado"""
    # Verificar se há amostras suficientes
    samples = []
    # Validar amostras
    # Buscar em duas pastas (processadas ou originais)
    samples = []

    # Prioridade 1: Amostras já processadas pelo frontend/backend
    if os.path.exists(VOICE_SAMPLES_DIR):
        samples = [f for f in os.listdir(VOICE_SAMPLES_DIR) if f.endswith('.wav')]

    # Prioridade 2: Buscar na pasta original se não achar
    if not samples:
        original_samples_dir = os.path.join(BASE_DIR, 'voice_samples')
        if os.path.exists(original_samples_dir):
             samples = [f for f in os.listdir(original_samples_dir) if f.endswith('.wav')]

    if len(samples) < 3:
        return jsonify({
            "status": "error",
            "message": f"Mínimo 3 amostras necessárias. Você tem {len(samples)}."
        }), 400

    # Iniciar processamento assíncrono para streaming de logs
    thread = threading.Thread(target=process_voice_async, args=(samples, VOICE_SAMPLES_DIR))
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "pending",
        "message": "Criação do modelo iniciada em segundo plano...",
        "log_url": "/api/logs"
    })

def process_voice_async(samples, samples_dir):
    """Processa voz em background e gera logs"""
    with app.app_context():
        try:
            state_manager.clear_logs()
            state_manager.update_status("processing_voice")
            state_manager.add_log("🎤 INICIANDO CRIAÇÃO DE MODELO DE VOZ...")
            state_manager.add_log(f"📂 Diretório de amostras: {samples_dir}")
            state_manager.add_log(f"📊 Amostras detectadas: {len(samples)}")

            # 1. PROCESSAMENTO DE ÁUDIO
            state_manager.add_log("\n🔇 [STAGE 1] TRATAMENTO DE ÁUDIO")
            state_manager.add_log("--------------------------------")

            from src.modules.voice_processor import VoiceProcessor
            processor = VoiceProcessor()
            processed_samples = []

            for i, sample in enumerate(samples, 1):
                input_path = os.path.join(samples_dir, sample)
                output_name = f"voice_sample_{i}_pro.wav"
                output_path = os.path.join(VOICE_MODELS_DIR, output_name) # Salvar direto no modelo

                state_manager.add_log(f"   Processando amostra {i}/{len(samples)}: {sample}")
                if processor.process_audio(input_path, output_path):
                     processed_samples.append(output_name)
                     state_manager.add_log(f"   ✅ Processado com sucesso! (Noise Reduction + EQ)")
                else:
                     state_manager.add_log(f"   ❌ Falha ao processar {sample}")

            if not processed_samples:
                state_manager.add_log("❌ Nenhuma amostra processada com sucesso. Abortando.")
                state_manager.update_status("error")
                return

            # 2. ANÁLISE DE VOZ
            state_manager.add_log("\n🧠 [STAGE 2] ANÁLISE DE PERFIL VOCAL")
            state_manager.add_log("--------------------------------")

            from src.modules.narrator import VoiceAnalyzer
            analyzer = VoiceAnalyzer()
            profile = analyzer.analyze_samples(VOICE_MODELS_DIR) # Analisar os já na pasta final

            pitch = profile.get('pitch_mean', 0)
            suggested = profile.get('suggested_voice', 'N/A')
            state_manager.add_log(f"   📊 Pitch Médio: {pitch:.1f} Hz")
            state_manager.add_log(f"   🗣️ Base Neural Sugerida: {suggested}")

            # 3. CRIAÇÃO DE CONFIG
            state_manager.add_log("\n💾 [STAGE 3] SALVANDO MODELO")
            state_manager.add_log("--------------------------------")

            model_config = {
                "created_at": datetime.now().isoformat(),
                "samples": processed_samples,
                "samples_dir": VOICE_MODELS_DIR,
                "model_name": "custom_voice_pro",
                "language": "pt-BR",
                "status": "ready",
                "profile": profile,
                "quality": "professional_mastered"
            }

            config_path = os.path.join(VOICE_MODELS_DIR, "custom_voice_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(model_config, f, ensure_ascii=False, indent=2)

            state_manager.add_log(f"   ✅ Configuração salva em: {config_path}")
            state_manager.add_log("\n✨ MODELO DE VOZ CRIADO COM SUCESSO!")
            state_manager.add_log("Agora você pode testar em '/voice-test'")
            state_manager.update_status("done")

        except Exception as e:
            state_manager.add_log(f"❌ ERRO FATAL: {str(e)}")
            state_manager.update_status("error")


@app.route('/api/voice/model')
def get_voice_model():
    """Retorna informações do modelo de voz"""
    config_path = os.path.join(VOICE_MODELS_DIR, "custom_voice_config.json")

    if not os.path.exists(config_path):
        return jsonify({"status": "not_found", "message": "Nenhum modelo criado ainda"})

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return jsonify({"status": "success", "model": config})


@app.route('/voice_samples/<path:filename>')
def serve_voice_sample(filename):
    """Serve arquivos de amostra de voz"""
    return send_from_directory(VOICE_SAMPLES_DIR, filename)


@app.route('/api/voice/test', methods=['POST'])
def test_voice_narration():
    """Testa a narração com a voz personalizada"""
    try:
        from src.modules.narrator import get_narrator

        data = request.json or {}
        text = data.get('text', 'Olá, esta é uma narração de teste com sua voz personalizada!')

        # Preparar logs para o console do frontend
        state_manager.clear_logs()
        state_manager.update_status("processing_test")
        state_manager.add_log(f"📝 Recebido texto: {text[:30]}...")

        narrator = get_narrator()
        output_path = os.path.join(TEMP_DIR, 'voice_test.mp3')

        # Callback para streaming de logs
        def log_step(msg):
            state_manager.add_log(msg)

        success = narrator.generate_narration(text, output_path, log_callback=log_step)

        if success:
             state_manager.add_log("✅ Áudio gerado e masterizado!")
             state_manager.update_status("done")
        else:
             state_manager.add_log("❌ Falha na geração do áudio.")
             state_manager.update_status("error")

        if success and os.path.exists(output_path):
            return jsonify({
                "status": "success",
                "message": "Narração gerada com sucesso!",
                "audio_url": "/temp/voice_test.mp3",
                "has_custom_voice": narrator.has_custom_voice
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao gerar narração"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/temp/<path:filename>')
def serve_temp(filename):
    """Serve arquivos temporários"""
    return send_from_directory(TEMP_DIR, filename)


# =====================
# STARTUP
# =====================
@app.route('/api/ingest', methods=['POST'])
def ingest_file():
    """Converte arquivo enviado para Markdown"""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Arquivo vazio"}), 400

    try:
        from src.modules.ingestor import get_ingestor
        ingestor = get_ingestor()

        temp_path = os.path.join(app.config['TEMP_DIR'], file.filename)
        file.save(temp_path)

        markdown_content = ingestor.convert_file(temp_path)
        os.remove(temp_path)

        return jsonify({
            "success": True,
            "content": markdown_content,
            "filename": file.filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/research', methods=['POST'])
def research_url():
    """Extrai conteúdo de uma URL em Markdown"""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL obrigatória"}), 400

    try:
        from src.modules.researcher import get_researcher
        researcher = get_researcher()

        # Crawl4AI é assíncrono, rodando no wrapper síncrono
        markdown_content = researcher.run_crawl(url)

        return jsonify({
            "success": True,
            "content": markdown_content,
            "url": url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================
# START SERVER
# =====================
if __name__ == '__main__':
    print("=" * 50)
    print("🎬 AI Video Clipper Studio V3")
    print("=" * 50)
    print(f"📂 Base: {BASE_DIR}")
    print(f"🐍 Python: {PYTHON_EXE}")
    print(f"📁 Temp: {TEMP_DIR}")
    print(f"📁 Exports: {EXPORTS_DIR}")
    print("=" * 50)
    print("🌐 Servidor: http://127.0.0.1:5000")
    print("=" * 50)

    app.run(debug=True, port=5000, threaded=True, host='0.0.0.0')
