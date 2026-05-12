# printer_interface.py
import win32print
import pywintypes
import os
from datetime import datetime

from constants import (
    PRINTER_NAME, PRINTER_DPI, LABEL_WIDTH_MM, LABEL_HEIGHT_MM,
    LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS,
    BOX_X_START, BOX_Y_START, BOX_WIDTH, BOX_HEIGHT,
    LINE_DIMENSION, BORDER_THICKNESS
)

# --- MODIFIED FUNCTION SIGNATURE AND USAGE ---
def print_zpl_to_printer_raw(printer_name, zpl_data, job_display_name="Python ZPL Labels Batch"):
    """
    Sends raw ZPL data to the specified Windows printer.
    This function handles opening, writing, and closing the printer connection.
    job_display_name: The name that will appear in the Windows print queue.
    """
    hPrinter = None
    try:
        print(f"Attempting to open printer: '{printer_name}' for raw ZPL...")
        hPrinter = win32print.OpenPrinter(printer_name)
        print("Printer opened successfully.")

        # Use the provided job_display_name for the print job
        DOC_INFO_RAW = (
            job_display_name, # Dynamic Name for the batch job
            None,
            "RAW"
        )

        print(f"Starting raw ZPL batch print job: '{job_display_name}'...")
        job_id = win32print.StartDocPrinter(hPrinter, 1, DOC_INFO_RAW)
        print(f"Raw ZPL batch print job started with ID: {job_id}")

        print("Writing combined ZPL data to printer...")
        win32print.WritePrinter(hPrinter, zpl_data.encode('utf-8'))
        print("Combined ZPL data written.")

        print("Ending raw ZPL batch print job...")
        win32print.EndDocPrinter(hPrinter)
        print("Raw ZPL batch print job ended successfully.")

    except pywintypes.error as e:
        print(f"\n--- Printing Error ---")
        print(f"Windows API Error: {e}")
        if e.winerror == 5:
            print("ERROR: Access denied. Try running your script as administrator.")
        elif e.winerror == 1797:
            print(f"ERROR: Printer name '{printer_name}' not found or invalid. Check spelling.")
        else:
            print(f"      Windows Error Code: {e.winerror} - {e.strerror}")
        print("--------------------")
    except Exception as e:
        print(f"\n--- Unexpected Error ---")
        print(f"An unexpected error occurred during printing: {e}")
        print("------------------------")
    finally:
        if hPrinter:
            win32print.ClosePrinter(hPrinter)

# --- MODIFIED FUNCTION SIGNATURE AND CALL TO print_zpl_to_printer_raw ---
def generate_and_print_labels(all_parsed_label_data, job_name_for_display, combined_colour_for_display):
    """
    Generates ZPL for each label in the provided data list and sends them
    as a single batch print job to the configured printer.
    Includes job_name_for_display and combined_colour_for_display for the print queue name.
    """
    if not all_parsed_label_data:
        print("No label data provided for printing.")
        return

    # Construct the dynamic print job name
    dynamic_job_name = f"{job_name_for_display}"
    if combined_colour_for_display: # Only add colour if it's not empty
        dynamic_job_name += f" - {combined_colour_for_display}"
    # Remove leading/trailing dashes if parts are empty (e.g., "JobName - " or " - Colour")
    dynamic_job_name = dynamic_job_name.strip(" -")
    if not dynamic_job_name: # Fallback if both are empty
        dynamic_job_name = "CNC Labels Batch Print"


    print("\n--- ZPL Label Generation for Multiple Labels ---")
    print(f"Label dimensions: {LABEL_WIDTH_MM}mm x {LABEL_HEIGHT_MM}mm ({LABEL_WIDTH_DOTS}x{LABEL_HEIGHT_DOTS} dots at {PRINTER_DPI} DPI).")
    print(f"Windows Print Job Name: '{dynamic_job_name}'")
    print("----------------------------------------------------------\n")

    all_labels_zpl = []
    current_date = datetime.now().strftime("%d/%m/%Y")

    for i, label_data in enumerate(all_parsed_label_data):
        print(f"\n--- Generating ZPL for Label {i+1} (Job: {label_data['JobName']}, Part: {label_data['PartName']}) ---")
        print(f"Edging variable set to: '{label_data.get('Edging', 'N/A')}'")

        border_zpl_segments = []
        edging_value = label_data.get('Edging', '') # Use .get() for safety

        # Conditional Border Drawing Logic (unchanged from your ZPL2ZebraV4.py)
        if edging_value == "EAR":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Top
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Left
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E1L":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom

        elif edging_value == "E1R":
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E2L":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Top
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom

        elif edging_value == "E1S":
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E2S":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Left
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E1L1S":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E1L2S":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Left
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        elif edging_value == "E2L1S":
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Top
            border_zpl_segments.append(f"^FO{BOX_X_START},{BOX_Y_START + BOX_HEIGHT}^GB{BOX_WIDTH},{LINE_DIMENSION},{BORDER_THICKNESS}^FS") # Bottom
            border_zpl_segments.append(f"^FO{BOX_X_START + BOX_WIDTH},{BOX_Y_START}^GB{LINE_DIMENSION},{BOX_HEIGHT},{BORDER_THICKNESS}^FS") # Right

        else:
            print(f"Warning: Unknown Edging value '{edging_value}'. No borders will be drawn for this label.")

        border_zpl = "\n".join(border_zpl_segments)

        current_label_zpl_string = f"""
^XA
^PW{LABEL_WIDTH_DOTS}~JSN^MCY^PMN^LH0,0^LRN^LT0^MNW^MTT^MMT^PON^LS0^PR2,2^JUS^MD0
{border_zpl}

^FO50,30^ADN,36,20^FD{label_data.get('JobName', '')}^FS
^FO50,80^ADN,20,12^FDPartName:^FS
^FO50,110^ADN,50,30^FD{label_data.get('PartName', '')}^FS
^FO50,170^ADN,22,12^FDLength:^FS
^FO270,170^ADN,20,12^FDWidth:^FS
^FO470,170^ADN,20,12^FDPartNum:^FS
^FO50,200^ADN,28,16^FD{label_data.get('Length', '')}^FS
^FO270,200^ADN,28,16^FD{label_data.get('Width', '')}^FS
^FO470,200^ADN,28,16^FD{label_data.get('PartNumber', '')}^FS
^FO50,280^ADN,20,12^FDEdging:^FS
^FO180,270^ADN,28,16^FD{label_data.get('Edging', '')}^FS
^FO530,270^ADN,28,16^FD{label_data.get('Layout', '')}^FS
^FO50,340^ADN,20,12^FDColour:^FS
^FO180,330^ADN,28,16^FD{label_data.get('Colour', '')}^FS
^FO50,400^ADN,20,12^FDComment:^FS
^FO50,440^ADN,28,16^FD{label_data.get('Comments', '')}^FS
^FO50,520^ADN,24,14^FDCreative Displays and Joinery^FS
^FO550,520^ADN,24,14^FD{current_date}^FS
^XZ
"""
        all_labels_zpl.append(current_label_zpl_string)
        print(f"ZPL for Label {i+1} generated and added to batch.")

    print("\n--- All individual label ZPLs generated. Combining for batch print. ---")
    final_combined_zpl = "".join(all_labels_zpl)

    print("\nAttempting to print the combined ZPL as a single batch...")
    # Pass the constructed dynamic_job_name here
    print_zpl_to_printer_raw(PRINTER_NAME, final_combined_zpl, dynamic_job_name)

    print("\n--- All labels processed and sent as a single batch. ---")