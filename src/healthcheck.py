import json, time, sys
from datetime import datetime

# Healthcheck: ensure state/state.json was updated in the last 3 hours

def main():
    try:
        with open("state/state.json") as f:
            state = json.load(f)
        last = state.get("last_run_timestamp")
        if not last:
            print("No timestamp in state"); sys.exit(1)
        if datetime.now().timestamp() - last > 3*3600:
            print("Stale state"); sys.exit(1)
        print("OK")
        sys.exit(0)
    except Exception as e:
        print(f"Healthcheck error: {e}"); sys.exit(1)

if __name__ == "__main__":
    main() 