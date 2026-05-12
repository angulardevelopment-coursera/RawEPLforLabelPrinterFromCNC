import os
import json
from datetime import datetime
from constants import APP_BASE_DIR, JOB_HISTORY_FILE

def log_job_details(job_name, edging_flag, colour, finish):
    """
    Logs job details to a JSONL (JSON Lines) history file.
    Each job entry is a single JSON object on a new line.
    """
    history_file_path = os.path.join(APP_BASE_DIR, JOB_HISTORY_FILE)
    
    # Ensure the directory exists
    os.makedirs(APP_BASE_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert edging_flag back to a human-readable string for history
    edging_type_map = {
        0: "No Edging",
        1: "Melamine",
        2: "Paint"
    }
    edging_type_str = edging_type_map.get(edging_flag, "Unknown")

    entry = {
        "timestamp": timestamp,
        "job_name": job_name,
        "edging_type": edging_type_str, # Use the string representation
        "colour": colour,
        "finish": finish
    }

    try:
        # Open in append mode ('a') and write as JSON line
        with open(history_file_path, 'a') as f:
            json.dump(entry, f)
            f.write('\n') # Write a newline to make it JSONL format
        print(f"Logged job details to history: {job_name}")
    except Exception as e:
        print(f"Error logging job details to {history_file_path}: {e}")