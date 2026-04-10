#!/usr/bin/env python3
"""
Transcription Server - Main Entry Point
FastAPI with async background task processing
"""

import os
import sys
import time
import signal
import subprocess
import uvicorn
import atexit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import settings
from app.logging.log_streamer import log_streamer

app = None


def write_pid():
    with open(settings.PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def read_pid():
    if os.path.exists(settings.PID_FILE):
        try:
            with open(settings.PID_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return None


def remove_pid():
    try:
        if os.path.exists(settings.PID_FILE):
            os.remove(settings.PID_FILE)
    except:
        pass


def is_running():
    pid = read_pid()
    if pid:
        try:
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
            if str(pid) in result.stdout:
                return True
        except:
            pass
        remove_pid()
    return False


def stop_server():
    pid = read_pid()
    if pid:
        try:
            print(f"Stopping server (PID: {pid})...")
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            time.sleep(1)
            print("Server stopped.")
        except Exception as e:
            print(f"Error: {e}")
    remove_pid()


def signal_handler(sig, frame):
    print("\n" + "="*60)
    print("Shutting down gracefully...")
    print("="*60)
    remove_pid()
    sys.exit(0)


def start_server():
    global app
    
    if is_running():
        print(f"Server already running (PID: {read_pid()})")
        return
    
    write_pid()
    atexit.register(remove_pid)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create app (returns both FastAPI and Socket.IO wrapped ASGI)
    from app import create_app
    fastapi_app, asgi_app = create_app()
    app = asgi_app  # Use the ASGI app with Socket.IO
    
    print("=" * 60)
    print("  TRANSCRIPTION SERVER")
    print("=" * 60)
    print(f"  PID:      {os.getpid()}")
    print(f"  Host:     {settings.HOST}")
    print(f"  Port:     {settings.PORT}")
    print(f"  Workers:  {settings.NUM_WORKERS}")
    print(f"  Logs:     {settings.LOGS_DIR}")
    print("=" * 60)
    print(f"  API:       http://{settings.HOST}:{settings.PORT}")
    print(f"  Dashboard: http://localhost:3000")
    print(f"  Socket.IO: ws://{settings.HOST}:{settings.PORT}/socket.io")
    print("=" * 60)
    print("  ✓ FastAPI with async task processing")
    print("  ✓ Socket.IO for live logs")
    print("  ✓ MSSQL database logging")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    log_streamer.info("Main", "Server started with FastAPI + Socket.IO")
    
    # Run with Uvicorn - simple and clean
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )


def show_status():
    if is_running():
        print(f"Server RUNNING (PID: {read_pid()})")
    else:
        print("Server NOT RUNNING")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "stop":
            stop_server()
        elif cmd == "status":
            show_status()
        elif cmd == "restart":
            stop_server()
            time.sleep(2)
            start_server()
        else:
            print("Usage: python run.py [start|stop|restart|status]")
    else:
        start_server()


if __name__ == "__main__":
    main()


def write_pid():
    with open(settings.PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def read_pid():
    if os.path.exists(settings.PID_FILE):
        try:
            with open(settings.PID_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return None


def remove_pid():
    try:
        if os.path.exists(settings.PID_FILE):
            os.remove(settings.PID_FILE)
    except:
        pass


def is_running():
    pid = read_pid()
    if pid:
        try:
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
            if str(pid) in result.stdout:
                return True
        except:
            pass
        remove_pid()
    return False


def stop_server():
    pid = read_pid()
    if pid:
        try:
            print(f"Stopping server (PID: {pid})...")
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            time.sleep(1)
            print("Server stopped.")
        except Exception as e:
            print(f"Error: {e}")
    remove_pid()


def worker_process(worker_id):
    """Worker process function - runs in separate process"""
    import sys
    print(f"[WORKER {worker_id}] 🟢 PROCESS STARTED - checking queue...", flush=True)
    sys.stdout.flush()
    log_streamer.info("Worker", f"Worker {worker_id} process started")
    
    check_count = 0
    while True:
        try:
            check_count += 1
            if check_count % 12 == 0:
                print(f"[WORKER {worker_id}] ✓ Still alive, queue size: {task_queue.qsize()}", flush=True)
                sys.stdout.flush()
            
            try:
                # Block for up to 5 seconds waiting for a job
                job = task_queue.get(timeout=5)
                print(f"[WORKER {worker_id}] 🎯 GOT JOB: {job['callId']}", flush=True)
                sys.stdout.flush()
            except:
                # Queue timeout, loop again
                time.sleep(0.1)
                continue
            
            try:
                print(f"[WORKER {worker_id}] 🔄 PROCESSING {job['callId']}", flush=True)
                sys.stdout.flush()
                log_streamer.info("Worker", f"Worker {worker_id}: 🟡 PROCESSING → {job['callId']}")
                
                # Process the call
                process_call(job, worker_id)
                
                print(f"[WORKER {worker_id}] ✅ COMPLETED {job['callId']}", flush=True)
                sys.stdout.flush()
                log_streamer.info("Worker", f"Worker {worker_id}: ✅ DONE with {job['callId']}")
            except Exception as e:
                print(f"[WORKER {worker_id}] ❌ ERROR: {e}", flush=True)
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                log_streamer.error("Worker", f"Worker {worker_id}: ❌ Error: {e}")
            finally:
                try:
                    task_queue.task_done()
                except:
                    pass
                    
        except Exception as e:
            print(f"[WORKER {worker_id}] ⚠️ LOOP ERROR: {e}", flush=True)
            sys.stdout.flush()
            log_streamer.error("Worker", f"Worker {worker_id}: ⚠️ Loop error: {e}")
            time.sleep(1)


def start_workers():
    """Start worker processes"""
    global worker_processes
    import sys
    
    print(f"\n{'='*60}", flush=True)
    print(f"STARTING {settings.NUM_WORKERS} WORKER PROCESSES", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()
    
    for i in range(settings.NUM_WORKERS):
        p = multiprocessing.Process(target=worker_process, args=(i + 1,), daemon=True)
        p.start()
        worker_processes.append(p)
        print(f"[MAIN] ✓ Started worker process {i+1} (PID: {p.pid})", flush=True)
        sys.stdout.flush()
        log_streamer.info("Main", f"Started worker process {i + 1} (PID: {p.pid})")
    
    print(f"\n{'='*60}", flush=True)
    print(f"ALL {len(worker_processes)} WORKERS STARTED - READY FOR JOBS", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()


def signal_handler(sig, frame):
    import sys
    print("\n" + "="*60)
    print("Shutting down gracefully...")
    print("="*60)
    
    # Terminate worker processes
    for p in worker_processes:
        if p.is_alive():
            print(f"[MAIN] Terminating worker process {p.pid}...")
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                p.kill()
    
    print("All workers stopped")
    sys.stdout.flush()
    remove_pid()
    sys.exit(0)


def start_server():
    global app, server_thread
    import sys
    import app as app_module
    
    if is_running():
        print(f"Server already running (PID: {read_pid()})")
        return
    
    write_pid()
    atexit.register(remove_pid)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # IMPORTANT: Create multiprocessing Queue BEFORE creating app or spawning workers
    print("[MAIN] Setting up multiprocessing queue...")
    app_module.task_queue = multiprocessing.Queue()
    print(f"[MAIN] ✓ Queue created and ready to share with workers")
    sys.stdout.flush()
    
    # Create app (now it can use the queue)
    app = create_app()
    
    # Start workers (they inherit the queue reference)
    start_workers()
    
    print("=" * 60)
    print("  TRANSCRIPTION SERVER")
    print("=" * 60)
    print(f"  PID:      {os.getpid()}")
    print(f"  Host:     {settings.HOST}")
    print(f"  Port:     {settings.PORT}")
    print(f"  Workers:  {settings.NUM_WORKERS}")
    print(f"  Logs:     {settings.LOGS_DIR}")
    print("=" * 60)
    print(f"  API:       http://{settings.HOST}:{settings.PORT}")
    print(f"  Dashboard: http://localhost:3000")
    print("=" * 60)
    print("  ✓ FastAPI with Uvicorn (in separate thread)")
    print("  ✓ Worker processes (multiprocessing with shared queue)")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    log_streamer.info("Main", "Server started with FastAPI + Worker processes")
    
    # Run Uvicorn in a separate thread
    server_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": app,
            "host": settings.HOST,
            "port": settings.PORT,
            "log_level": "info"
        },
        daemon=False
    )
    server_thread.start()
    print("[MAIN] ✓ Uvicorn API server started in separate thread\n")
    sys.stdout.flush()
    
    # Keep main thread alive and monitor workers
    print("[MAIN] 🟢 Main thread: monitoring workers...")
    sys.stdout.flush()
    try:
        while True:
            time.sleep(1)
            # Check if any workers died and restart them
            for i, p in enumerate(worker_processes):
                if not p.is_alive():
                    print(f"[MAIN] ⚠️ Worker process {i+1} died! Restarting...")
                    worker_processes.pop(i)
                    new_p = multiprocessing.Process(target=worker_process, args=(i+1,), daemon=True)
                    new_p.start()
                    worker_processes.insert(i, new_p)
    except KeyboardInterrupt:
        print("\n[MAIN] Received Ctrl+C, shutting down...")
        sys.exit(0)


def show_status():
    if is_running():
        print(f"Server RUNNING (PID: {read_pid()})")
    else:
        print("Server NOT RUNNING")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "stop":
            stop_server()
        elif cmd == "status":
            show_status()
        elif cmd == "restart":
            stop_server()
            time.sleep(2)
            start_server()
        else:
            print("Usage: python run.py [start|stop|restart|status]")
    else:
        start_server()


if __name__ == "__main__":
    main()