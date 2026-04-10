"""
Async background task processor for FastAPI
Processes transcription calls from the queue sequentially
"""

import asyncio
from app.logging.log_streamer import log_streamer
from app.workers.call_processor import process_call


async def process_tasks_loop(task_queue):
    """
    Continuously process tasks from the queue.
    Runs as a background task in FastAPI.
    """
    log_streamer.info("TaskProcessor", "🟢 Background task processor started")
    print("[TaskProcessor] 🟢 Started - waiting for jobs...")
    
    while True:
        try:
            # Wait for a job from the queue (non-blocking with timeout)
            try:
                job = task_queue.get_nowait()
            except asyncio.QueueEmpty:
                # No job available, sleep and try again
                await asyncio.sleep(0.5)
                continue
            
            call_id = job.get("callId")
            rec_url = job.get("recUrl")
            
            print(f"[TaskProcessor] 🎯 Got job: {call_id}", flush=True)
            log_streamer.info("TaskProcessor", f"🟡 Processing → {call_id}")
            
            # Process in a background task (doesn't block FastAPI requests)
            await asyncio.to_thread(process_call, job, worker_id=1)
            
            print(f"[TaskProcessor] ✅ Completed: {call_id}", flush=True)
            log_streamer.info("TaskProcessor", f"✅ Completed → {call_id}")
            
        except Exception as e:
            print(f"[TaskProcessor] ❌ Error: {e}", flush=True)
            log_streamer.error("TaskProcessor", f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)


async def lifespan(app):
    """
    FastAPI lifespan handler - runs background tasks
    """
    from app import task_queue
    
    # Startup
    print("\n[Lifespan] Starting background task processor...")
    task_processor = asyncio.create_task(process_tasks_loop(task_queue))
    print("[Lifespan] ✓ Background task processor created")
    
    yield
    
    # Shutdown
    print("\n[Lifespan] Shutting down background task processor...")
    task_processor.cancel()
    try:
        await task_processor
    except asyncio.CancelledError:
        pass
    print("[Lifespan] ✓ Background task processor stopped")
