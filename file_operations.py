# file_operations.py
import os
import json # Not directly used by functions here, but common for file ops
import csv  # Not directly used by functions here, but common for file ops
from qtpy.QtWidgets import QMessageBox # For warnings in load_edging_or_paint_data

def load_edging_or_paint_data(filepath):
    """
    Loads data from Edging.txt or Paint.txt.
    Expected format: PartName_Base,Edging_If_L_ge_W,Edging_If_W_gt_L[,Comment]
    Stops reading at "EOF" or empty lines.
    Returns a list of tuples: (base_part_name, edging_L_ge_W, edging_W_gt_L, comment)
    Automatically adds empty string for comment if not present (for backward compatibility).
    """
    lookup_data = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip() 
                if not line or line.upper() == "EOF": 
                    break
                
                parts = line.split(',')
                base_name = parts[0].strip() if len(parts) > 0 else ""
                val_L_ge_W = parts[1].strip() if len(parts) > 1 else ""
                val_W_gt_L = parts[2].strip() if len(parts) > 2 else ""
                comment = parts[3].strip() if len(parts) > 3 else "" 

                lookup_data.append((base_name, val_L_ge_W, val_W_gt_L, comment))
                
    except FileNotFoundError:
        QMessageBox.warning(None, "File Not Found", f"Error: Edging/Paint data file '{os.path.basename(filepath)}' not found in the application directory.\nExpected: {filepath}")
        print(f"Error: Edging/Paint file not found at {filepath}")
    except Exception as e:
        QMessageBox.critical(None, "File Read Error", f"An error occurred while reading '{os.path.basename(filepath)}': {e}")
        print(f"Error reading {filepath}: {e}")
    return lookup_data

def parse_tlf_file(filepath, job_name, starting_part_number):
    """
    Parses a single .tlf file based on the VBA logic.
    Returns a list of dictionaries, one for each part found.
    """
    parsed_parts = []
    lines = []
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Could not read file {filepath}: {e}")
        raise

    current_part_number = starting_part_number

    for i in range(len(lines)):
        line = lines[i].strip()

        if line == "STR" and (i + 3 < len(lines) and lines[i + 3].strip() == "TEXT"):
            try:
                part_name_layout_line = lines[i + 1].strip()
                splitter_part_layout = part_name_layout_line.split(".")
                part_name = splitter_part_layout[0]
                layout = splitter_part_layout[1] if len(splitter_part_layout) > 1 else ""

                dimensions_line = lines[i + 21].strip()
                splitter_dimensions = dimensions_line.split("x")

                length = int(float(splitter_dimensions[0]))
                width = int(float(splitter_dimensions[1]))
                height = int(float(splitter_dimensions[2])) if len(splitter_dimensions) > 2 else 0

                part_data = {
                    "PartNumber": current_part_number,
                    "PartName": part_name,
                    "Length": length,
                    "Width": width,
                    "Height": height,
                    "Edging": "", 
                    "Comments": "", 
                    "Layout": layout,
                    "Colour": "", 
                    "JobName": job_name
                }
                parsed_parts.append(part_data)
                current_part_number += 1

            except (IndexError, ValueError) as e:
                print(f"  Warning: Skipping problematic block starting at line {i+1} in {os.path.basename(filepath)}. Error: {e}")
                continue
            except Exception as e:
                print(f"  An unexpected error occurred while parsing block at line {i+1} in {os.path.basename(filepath)}: {e}")
                continue

    return parsed_parts