import sys
import os
import re

from qtpy.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QLabel, QFileDialog, QLineEdit, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QMessageBox, QDialog
)
from qtpy.QtCore import Qt

from constants import APP_BASE_DIR, CONFIG_FILE, PRINTER_NAME
from dialogs import JobDetailsDialog, EditEdgingPaintDialog, JobHistoryDialog
from file_operations import parse_tlf_file, load_edging_or_paint_data
from config_manager import load_config, save_config
from label_logic import apply_edging_or_paint_logic
from printer_interface import generate_and_print_labels
from history_manager import log_job_details

class CNCLabelPrinterApp(QMainWindow):
    LABEL_HEADERS = [
        "PartNumber", "PartName", "Length", "Width", "Height",
        "Edging", "Comments", "Layout", "Colour", "JobName"
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Label Printer")
        self.remembered_parent_folder = ""
        self.current_job_folder_selected = ""
        self.all_parsed_label_data = []

        # Current job details, populated after JobDetailsDialog is accepted
        self._current_edging_flag = 0
        self._current_combined_colour_finish = ""
        self._current_job_name = ""
        self._current_raw_colour_input = ""
        self._current_raw_finish_input = ""

        # Last remembered job details (ONLY for loading the 'last_remembered_folder' from config)
        # These will no longer be used for pre-filling JobDetailsDialog
        self._last_remembered_job_name = ""
        self._last_remembered_edging_flag = 0
        self._last_remembered_colour_input = ""
        self._last_remembered_finish_input = ""

        self.init_ui()
        self._load_app_config()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        central_widget.setStyleSheet("background-color: #006400;") # Deep Green

        # Define the button style ONCE here
        button_style = """
            QPushButton {
                background-color: #09911d; /* Poblano Green - Your current base */
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #004d00;
            }
            QPushButton:hover {
                background-color: #8BC34A; /* A lighter, slightly yellowish-green */
            }
            QPushButton:pressed {
                background-color: #689F38; /* A darker, more olive-like green */
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #A0A0A0;
            }
        """

        # Folder path display (now a standalone line, not grouped with button)
        self.folder_path_display = QLineEdit()
        self.folder_path_display.setPlaceholderText("No 'Home' folder remembered. Select a job folder.")
        self.folder_path_display.setReadOnly(True)
        self.folder_path_display.setStyleSheet("background-color: white;")
        main_layout.addWidget(self.folder_path_display)

        # Select All Checkbox
        select_all_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.setChecked(False)
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_tlf_selection)
        self.select_all_checkbox.setStyleSheet("color: white;")
        select_all_layout.addWidget(self.select_all_checkbox)
        select_all_layout.addStretch(1)
        main_layout.addLayout(select_all_layout)

        # Data Grid
        self.data_grid = QTableWidget()
        self.data_grid.setColumnCount(2)
        self.data_grid.setHorizontalHeaderLabels(["Select", "TLF File Name"])
        self.data_grid.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.data_grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.data_grid.setStyleSheet("background-color: #E8F5E9;")
        main_layout.addWidget(self.data_grid, 10)

        # --- Horizontal Layout for all primary buttons at the bottom ---
        bottom_buttons_layout = QHBoxLayout()
        
        self.select_folder_button = QPushButton("Select Job Folder")
        self.select_folder_button.clicked.connect(self.select_job_folder)
        self.select_folder_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.select_folder_button)

        self.edit_edging_button = QPushButton("Edit Edging File")
        self.edit_edging_button.clicked.connect(self.edit_edging_file)
        self.edit_edging_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.edit_edging_button)

        self.edit_paint_button = QPushButton("Edit Paint File")
        self.edit_paint_button.clicked.connect(self.edit_paint_file)
        self.edit_paint_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.edit_paint_button)

        self.process_files_button = QPushButton("Process Selected Files")
        self.process_files_button.clicked.connect(self.process_selected_files_and_prepare_data)
        self.process_files_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.process_files_button)

        self.view_history_button = QPushButton("View Job History")
        self.view_history_button.clicked.connect(self.view_job_history)
        self.view_history_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.view_history_button)

        self.print_labels_button = QPushButton("Print Labels")
        self.print_labels_button.clicked.connect(self.initiate_printing)
        self.print_labels_button.setEnabled(False) # Initially disabled
        self.print_labels_button.setStyleSheet(button_style)
        bottom_buttons_layout.addWidget(self.print_labels_button)
        
        main_layout.addStretch(1) # Pushes everything above to the top, and buttons to the bottom
        main_layout.addLayout(bottom_buttons_layout)
        # --- END Horizontal Layout ---

    def select_job_folder(self):
        initial_dir = self.remembered_parent_folder if os.path.exists(self.remembered_parent_folder) else os.getcwd()
        selected_job_folder = QFileDialog.getExistingDirectory(self, "Select Job Folder (Contains .tlf files)", initial_dir)

        if selected_job_folder:
            self.remembered_parent_folder = os.path.dirname(selected_job_folder)
            self.folder_path_display.setText(self.remembered_parent_folder)
            
            config = load_config()
            config['last_remembered_folder'] = self.remembered_parent_folder
            save_config(config)

            self.current_job_folder_selected = selected_job_folder
            print(f"User selected job folder: {self.current_job_folder_selected}")
            print(f"Remembering parent folder for next launch: {self.remembered_parent_folder}")

            self.scan_and_display_tlf_files(self.current_job_folder_selected)
            self.print_labels_button.setEnabled(False)
            self.all_parsed_label_data = []
        else:
            self.print_labels_button.setEnabled(False)
            self.all_parsed_label_data = []


    def scan_and_display_tlf_files(self, folder_path):
        self.data_grid.setRowCount(0)
        self.data_grid.setColumnCount(2)
        self.data_grid.setHorizontalHeaderLabels(["Select", "TLF File Name"])
        self.data_grid.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.data_grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        tlf_files = []
        try:
            for item in os.listdir(folder_path):
                if item.endswith(".tlf") and os.path.isfile(os.path.join(folder_path, item)):
                    tlf_files.append(item)
            
            # --- START FIX: Natural Sort for file names ---
            def natural_sort_key(s):
                """A key function to enable sorting strings containing numbers correctly."""
                return [int(text) if text.isdigit() else text.lower()
                        for text in re.split('([0-9]+)', s)]

            tlf_files.sort(key=natural_sort_key) # <-- Apply the natural sort key

            if not tlf_files:
                self.data_grid.setRowCount(1)
                no_files_item = QTableWidgetItem("No .tlf files found in this folder.")
                no_files_item.setFlags(no_files_item.flags() & ~Qt.ItemIsSelectable)
                self.data_grid.setItem(0, 0, no_files_item)
                self.data_grid.setSpan(0, 0, 1, 2)
                self.select_all_checkbox.setEnabled(False)
                self.select_all_checkbox.blockSignals(True)
                self.select_all_checkbox.setChecked(False)
                self.select_all_checkbox.blockSignals(False)
                self.process_files_button.setEnabled(False)
                print(f"No .tlf files found in {folder_path}")
                return

            self.select_all_checkbox.setEnabled(True)
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)
            self.process_files_button.setEnabled(True)

            self.data_grid.setRowCount(len(tlf_files))

            for row, file_name in enumerate(tlf_files):
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                self.data_grid.setItem(row, 0, checkbox_item)

                file_name_item = QTableWidgetItem(file_name)
                file_name_item.setFlags(file_name_item.flags() & ~Qt.ItemIsEditable)
                self.data_grid.setItem(row, 1, file_name_item)

            print(f"Found {len(tlf_files)} .tlf files in {folder_path} and displayed them with checkboxes.")

        except Exception as e:
            print(f"Error scanning .tlf files: {e}")
            self.data_grid.setRowCount(1)
            error_item = QTableWidgetItem(f"Error: {str(e)}")
            error_item.setFlags(error_item.flags() & ~Qt.ItemIsSelectable)
            self.data_grid.setItem(0, 0, error_item)
            self.data_grid.setSpan(0, 0, 1, 2)
            self.select_all_checkbox.setEnabled(False)
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)
            self.process_files_button.setEnabled(False)


    def toggle_all_tlf_selection(self, state):
        check_state = Qt.Checked if self.select_all_checkbox.isChecked() else Qt.Unchecked
        print(f"Select All checkbox state determined for table: {check_state}. Toggling all table checkboxes.")

        for row in range(self.data_grid.rowCount()):
            item = self.data_grid.item(row, 0)
            if item:
                item.setCheckState(check_state)

    def _load_app_config(self):
        """Loads configuration specific to the app's state, only 'last_remembered_folder'."""
        config = load_config()
        self.remembered_parent_folder = config.get('last_remembered_folder', '')
        self.folder_path_display.setText(self.remembered_parent_folder)
        print(f"Loaded config: last_remembered_folder='{self.remembered_parent_folder}'")

        # The following 'last_remembered' values are no longer used for pre-filling dialog
        # but are kept in config for historical purposes if ever needed.
        self._last_remembered_job_name = config.get('last_job_name', '')
        self._last_remembered_edging_flag = config.get('last_edging_flag', 0)
        self._last_remembered_colour_input = config.get('last_colour_input', '')
        self._last_remembered_finish_input = config.get('last_finish_input', '')
        # We print them for debugging, but they won't affect the dialog defaults anymore.
        print(f"Loaded (but not used for dialog defaults) job details: Name='{self._last_remembered_job_name}', Edging={self._last_remembered_edging_flag}, Colour='{self._last_remembered_colour_input}', Finish='{self._last_remembered_finish_input}'")


    def view_job_history(self):
        """Opens the JobHistoryDialog to display past job entries."""
        history_dialog = JobHistoryDialog(parent=self)
        history_dialog.exec_()


    def process_selected_files_and_prepare_data(self):
        if not self.current_job_folder_selected or not os.path.isdir(self.current_job_folder_selected):
            QMessageBox.warning(self, "No Folder Selected", "Please select a job folder first.")
            print("No job folder selected or invalid path.")
            self.print_labels_button.setEnabled(False)
            return

        selected_tlf_files = []
        for row in range(self.data_grid.rowCount()):
            checkbox_item = self.data_grid.item(row, 0)
            file_name_item = self.data_grid.item(row, 1)

            if checkbox_item and file_name_item and checkbox_item.checkState() == Qt.Checked:
                file_name = file_name_item.text()
                full_file_path = os.path.join(self.current_job_folder_selected, file_name)
                if os.path.isfile(full_file_path):
                    selected_tlf_files.append(full_file_path)

        if not selected_tlf_files:
            QMessageBox.information(self, "No Files Selected", "Please select at least one .tlf file for processing.")
            print("No .tlf files selected for processing.")
            self.print_labels_button.setEnabled(False)
            self.all_parsed_label_data = []
            self.display_parsed_data_in_grid()
            return

        # Determine the suggested job name from the selected folder
        suggested_job_name_from_folder = os.path.basename(self.current_job_folder_selected)
        print(f"Suggested job name from folder: '{suggested_job_name_from_folder}'")

        dialog = JobDetailsDialog(
            # Job Name: Always auto-fill from folder name
            default_job_name=suggested_job_name_from_folder,
            # Edging Flag: Always default to 0 (No Edging)
            default_edging_flag=0,
            # Colour: Always start blank
            default_colour="",
            # Finish: Always start blank
            default_finish="",
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            job_name = dialog.job_name
            edging_flag = dialog.edging_flag
            colour_input = dialog.colour
            finish_input = dialog.finish

            # We still save these to config.json for 'last_job_name' etc.,
            # but they won't be used for pre-filling the dialog next time.
            config = load_config()
            config['last_job_name'] = job_name
            config['last_edging_flag'] = edging_flag
            config['last_colour_input'] = colour_input
            config['last_finish_input'] = finish_input
            save_config(config)

            # Log to history (this is separate from config)
            log_job_details(job_name, edging_flag, colour_input, finish_input)

            self._current_job_name = job_name
            self._current_edging_flag = edging_flag
            self._current_raw_colour_input = colour_input
            self._current_raw_finish_input = finish_input

            self._current_combined_colour_finish = ""
            if colour_input and finish_input:
                self._current_combined_colour_finish = f"{colour_input} {finish_input}"
            elif colour_input:
                self._current_combined_colour_finish = colour_input
            elif finish_input:
                self._current_combined_colour_finish = finish_input
            self._current_combined_colour_finish = self._current_combined_colour_finish.strip()

            print(f"\nDialog Accepted:")
            print(f"  Job Name: {self._current_job_name}")
            print(f"  Edging Flag: {self._current_edging_flag}")
            print(f"  Combined Colour: '{self._current_combined_colour_finish}'")

        else:
            print("Job Details input cancelled.")
            self.print_labels_button.setEnabled(False)
            self.all_parsed_label_data = []
            self.display_parsed_data_in_grid()
            return

        self.all_parsed_label_data = []
        part_number_counter = 1

        print(f"Processing {len(selected_tlf_files)} selected .tlf files for Job: {self._current_job_name}")

        for file_path in selected_tlf_files:
            print(f"  Parsing file: {os.path.basename(file_path)}")
            try:
                parsed_parts_from_file = parse_tlf_file(file_path, self._current_job_name, part_number_counter)
                self.all_parsed_label_data.extend(parsed_parts_from_file)
                if parsed_parts_from_file:
                    part_number_counter = parsed_parts_from_file[-1]['PartNumber'] + 1
            except Exception as e:
                print(f"  Error parsing {os.path.basename(file_path)}: {e}")
        #START OF NEW CODE        
        self.all_parsed_label_data.sort(key=lambda part: part['PartNumber'])
        print("Final parsed label data sorted by PartNumber.")
        #END OF NEW CODE
        self._reapply_edging_to_all_parts()

        if self.all_parsed_label_data:
            self.print_labels_button.setEnabled(True)
            QMessageBox.information(self, "Processing Complete", "Files processed. You can now review and print labels.")
        else:
            self.print_labels_button.setEnabled(False)
            QMessageBox.warning(self, "No Data Processed", "No valid label data was generated from the selected files.")


    def _reapply_edging_to_all_parts(self):
        """
        Re-applies the current edging/paint rules to all parsed parts.
        This is called after initial parsing or after editing Edging/Paint files.
        """
        if not self.all_parsed_label_data:
            print("No parsed data to re-apply edging to.")
            self.display_parsed_data_in_grid()
            self.print_labels_button.setEnabled(False)
            return

        for part in self.all_parsed_label_data:
            part['Colour'] = ""
            part['Edging'] = ""
            part['Comments'] = ""

        if self._current_edging_flag in [1, 2]:
            for part in self.all_parsed_label_data:
                part['Colour'] = self._current_combined_colour_finish
        
        edging_file_to_load = ""
        if self._current_edging_flag == 1:
            edging_file_to_load = os.path.join(APP_BASE_DIR, "Edging.txt")
            print("Re-applying Melamine edging rules...")
        elif self._current_edging_flag == 2:
            edging_file_to_load = os.path.join(APP_BASE_DIR, "Paint.txt")
            print("Re-applying Paint rules...")
        else:
            print("No edging/paint type selected. 'Edging' and 'Comments' column will be cleared.")
            self.display_parsed_data_in_grid()
            return

        if edging_file_to_load:
            loaded_edging_map = load_edging_or_paint_data(edging_file_to_load)
            apply_edging_or_paint_logic(self.all_parsed_label_data, loaded_edging_map)

        self.display_parsed_data_in_grid()
        if self.all_parsed_label_data:
            self.print_labels_button.setEnabled(True)
        else:
            self.print_labels_button.setEnabled(False)


    def display_parsed_data_in_grid(self):
        """Populates the QTableWidget with the fully parsed label data."""
        self.data_grid.setRowCount(0)
        self.data_grid.setColumnCount(len(self.LABEL_HEADERS))
        self.data_grid.setHorizontalHeaderLabels(self.LABEL_HEADERS)

        for i, header in enumerate(self.LABEL_HEADERS):
            if header in ["PartNumber", "Length", "Width", "Height", "Layout"]:
                self.data_grid.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                self.data_grid.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        self.data_grid.setRowCount(len(self.all_parsed_label_data))

        for row_idx, label_dict in enumerate(self.all_parsed_label_data):
            for col_idx, header in enumerate(self.LABEL_HEADERS):
                value = label_dict.get(header, "")
                item = QTableWidgetItem(str(value))

                if header in ["Edging", "Comments", "Colour"]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                self.data_grid.setItem(row_idx, col_idx, item)

        print(f"Displaying {len(self.all_parsed_label_data)} parsed items in the data grid.")
        self.select_all_checkbox.setEnabled(False)
        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setChecked(False)
        self.select_all_checkbox.blockSignals(False)


    def edit_edging_file(self):
        file_path = os.path.join(APP_BASE_DIR, "Edging.txt")
        dialog = EditEdgingPaintDialog(file_path, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            print(f"Edging.txt saved. Re-applying rules to parts.")
            self._reapply_edging_to_all_parts()


    def edit_paint_file(self):
        file_path = os.path.join(APP_BASE_DIR, "Paint.txt")
        dialog = EditEdgingPaintDialog(file_path, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            print(f"Paint.txt saved. Re-applying rules to parts.")
            self._reapply_edging_to_all_parts()


    def initiate_printing(self):
        self._capture_grid_edits_to_data()

        if not self.all_parsed_label_data:
            QMessageBox.warning(self, "No Labels to Print", "No label data has been processed or is available for printing.")
            print("Print button clicked but no label data available.")
            return

        print("\n--- Initiating Label Printing ---")
        generate_and_print_labels(
            self.all_parsed_label_data,
            self._current_job_name,
            self._current_combined_colour_finish
        )
        QMessageBox.information(self, "Print Job Sent", "Label print job has been sent to the printer.")

    def _capture_grid_edits_to_data(self):
        """
        Captures any changes made by the user directly in the QTableWidget
        back into self.all_parsed_label_data before printing.
        Only applies to editable columns: Edging, Comments, Colour.
        """
        if not self.all_parsed_label_data or self.data_grid.rowCount() == 0:
            return

        print("Capturing potential grid edits back into data model...")
        for row_idx in range(self.data_grid.rowCount()):
            for col_idx, header in enumerate(self.LABEL_HEADERS):
                if header in ["Edging", "Comments", "Colour"]:
                    item = self.data_grid.item(row_idx, col_idx)
                    if item:
                        current_value = self.all_parsed_label_data[row_idx].get(header, "")
                        new_value = item.text()
                        if current_value != new_value:
                            self.all_parsed_label_data[row_idx][header] = new_value
                            print(f"  Row {row_idx}, {header}: '{current_value}' -> '{new_value}'")
        print("Grid edits captured.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCLabelPrinterApp()
    
    window.showMaximized()
    sys.exit(app.exec_())