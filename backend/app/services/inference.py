import threading

# Apple's Metal (MPS) backend aborts the whole process if two threads encode GPU work at
# once ("A command encoder is already encoding to this command buffer"). FastAPI serves
# requests from a thread pool, so every model call takes this lock: requests queue, not crash.
gpu_lock = threading.Lock()
