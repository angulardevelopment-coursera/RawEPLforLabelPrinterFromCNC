import os
import json
from constants import APP_BASE_DIR, CONFIG_FILE

def load_config():
    """Loads application configuration from config.json."""
    config_path = os.path.join(APP_BASE_DIR, CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print("Loaded config from config.json.")
            return config
        except json.JSONDecodeError:
            print("Error decoding config.json, creating new config.")
            return {}
        except Exception as e:
            print(f"Error loading config.json: {e}, creating new config.")
            return {}
    print("config.json not found, returning empty config.")
    return {}

def save_config(config_data):
    """Saves application configuration to config.json."""
    config_path = os.path.join(APP_BASE_DIR, CONFIG_FILE)
    os.makedirs(APP_BASE_DIR, exist_ok=True) # Ensure the directory exists
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Saved config to config.json.")
    except Exception as e:
        print(f"Error saving config to config.json: {e}")