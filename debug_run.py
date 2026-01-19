import sys
import subprocess
import os

with open("debug_result.txt", "w") as f:
    f.write(f"Debug Script Running. Python: {sys.executable}\n")
    f.write(f"CWD: {os.getcwd()}\n")

    try:
        proc = subprocess.Popen([sys.executable, 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        try:
            stdout, stderr = proc.communicate(timeout=15)
            # If we get here, it finished (crashed)
            f.write(f"FAILURE: app.py exited immediately! Code: {proc.returncode}\n")
            f.write(f"STDOUT:\n{stdout}\n")
            f.write(f"STDERR:\n{stderr}\n")
        except subprocess.TimeoutExpired:
            f.write("SUCCESS: app.py is running (timeout expired means it kept running)\n")
            proc.kill()
            
    except Exception as e:
        f.write(f"Wrapper failed: {e}\n")
