import os
import shutil
import subprocess
from pathlib import Path

def diagnose():
    print("🔍 Diagnosing Node.js environment...")
    
    # 1. Check PATH
    print(f"PATH: {os.environ.get('PATH', '')[:200]}...")
    
    # 2. Check shutil.which
    node_path = shutil.which("node")
    print(f"shutil.which('node'): {node_path}")
    
    # 3. Try subprocess
    try:
        ver = subprocess.check_output(["node", "-v"], stderr=subprocess.STDOUT, text=True).strip()
        print(f"Subprocess node -v: {ver}")
    except Exception as e:
        print(f"Subprocess node -v failed: {e}")

    # 4. Check bin/node/bin/node specifically
    local_node = Path(os.getcwd()) / "bin" / "node" / "bin" / "node"
    print(f"Local node exists: {local_node.exists()}")
    if local_node.exists():
        print(f"Local node permissions: {oct(os.stat(local_node).st_mode)}")
        try:
            ver = subprocess.check_output([str(local_node), "-v"], stderr=subprocess.STDOUT, text=True).strip()
            print(f"Local node -v directly: {ver}")
        except Exception as e:
            print(f"Local node -v directly failed: {e}")

if __name__ == "__main__":
    diagnose()
