import os
import time
import pickle

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

def save_cache(name: str, data: dict):
    path = os.path.join(CACHE_DIR, f"{name}.pkl")
    try:
        t0 = time.time()
        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        elapsed = round(time.time() - t0, 3)
        print(f"[CACHE] Saved {name} cache ({size_mb:.1f} MB) in {elapsed}s -> {path}")
    except Exception as e:
        print(f"[CACHE ERROR] Failed to save {name} cache: {e}")

def load_cache(name: str):
    path = os.path.join(CACHE_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        return None
    try:
        size_mb = os.path.getsize(path) / (1024 * 1024)
        t0 = time.time()
        with open(path, "rb") as f:
            data = pickle.load(f)
        elapsed = round(time.time() - t0, 3)
        print(f"[CACHE] Loaded {name} ({size_mb:.1f} MB) in {elapsed}s")
        return data
    except Exception as e:
        print(f"[CACHE ERROR] Failed to load {name} cache: {e}")
        return None
