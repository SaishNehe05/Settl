"""
Settl — Local Development Runner
Starts FastAPI backend on :8000 and Next.js frontend on :3000
"""
import subprocess
import sys
import os
import signal

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_DIR = os.path.join(ROOT_DIR, "apps", "api")
WEB_DIR = os.path.join(ROOT_DIR, "apps", "web")

def main():
    print("=" * 60)
    print("  🚀 Starting Settl Development Environment")
    print("=" * 60)
    
    # 1. Start Backend
    venv_python = os.path.join(API_DIR, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"

    print(f"\n[1/2] Starting FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [
        venv_python, "-m", "uvicorn", "app.main:app",
        "--reload", "--port", "8000", "--host", "127.0.0.1"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=API_DIR)

    # 2. Start Frontend
    print(f"\n[2/2] Starting Next.js Merchant Portal on http://localhost:3000 ...")
    frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=WEB_DIR)

    print("\n" + "=" * 60)
    print("  ✅ Settl is running!")
    print("  • Frontend Portal: http://localhost:3000")
    print("  • Backend API:     http://localhost:8000")
    print("  • API Swagger:     http://localhost:8000/docs")
    print("=" * 60)
    print("Press Ctrl+C to terminate all services...\n")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping Settl services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
