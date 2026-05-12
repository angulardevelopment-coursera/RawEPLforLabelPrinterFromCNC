from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QDialogButtonBox, # QComboBox removed here
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTextEdit,
    QRadioButton, QButtonGroup # Added for radio buttons
)
from qtpy.QtCore import Qt

import os
import json

from constants import APP_BASE_DIR, JOB_HISTORY_FILE

class JobDetailsDialog(QDialog):
    def __init__(self, default_job_name="", default_edging_flag=0, default_colour="", default_finish="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Job Details")
        self.setMinimumWidth(400)

        self.job_name = default_job_name
        self.edging_flag = default_edging_flag
        self.colour = default_colour
        self.finish = default_finish

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Job Name
        job_name_layout = QHBoxLayout()
        job_name_layout.addWidget(QLabel("Job Name:"))
        self.job_name_input = QLineEdit(self.job_name)
        job_name_layout.addWidget(self.job_name_input)
        main_layout.addLayout(job_name_layout)

        # Edging Type (Radio Buttons)
        edging_type_layout = QHBoxLayout()
        edging_type_layout.addWidget(QLabel("Edging Type:"))

        self.edging_button_group = QButtonGroup(self) # Create a button group for exclusivity
        self.edging_radio_buttons = {} # To store references to radio buttons by their ID

        # No Edging Radio Button (ID 0)
        self.radio_no_edging = QRadioButton("No Edging (0)")
        self.edging_button_group.addButton(self.radio_no_edging, 0)
        self.edging_radio_buttons[0] = self.radio_no_edging
        edging_type_layout.addWidget(self.radio_no_edging)

        # Melamine Radio Button (ID 1)
        self.radio_melamine = QRadioButton("Melamine (1)")
        self.edging_button_group.addButton(self.radio_melamine, 1)
        self.edging_radio_buttons[1] = self.radio_melamine
        edging_type_layout.addWidget(self.radio_melamine)

        # Paint Radio Button (ID 2)
        self.radio_paint = QRadioButton("Paint (2)")
        self.edging_button_group.addButton(self.radio_paint, 2)
        self.edging_radio_buttons[2] = self.radio_paint
        edging_type_layout.addWidget(self.radio_paint)

        edging_type_layout.addStretch(1) # Push radio buttons to the left
        main_layout.addLayout(edging_type_layout)

        # Set initial checked state based on default_edging_flag
        if self.edging_flag in self.edging_radio_buttons:
            self.edging_radio_buttons[self.edging_flag].setChecked(True)
        else:
            self.radio_no_edging.setChecked(True) # Default to No Edging if invalid flag

        # Colour
        colour_layout = QHBoxLayout()
        colour_layout.addWidget(QLabel("Colour:"))
        self.colour_input = QLineEdit(self.colour)
        colour_layout.addWidget(self.colour_input)
        main_layout.addLayout(colour_layout)

        # Finish
        finish_layout = QHBoxLayout()
        finish_layout.addWidget(QLabel("Finish:"))
        self.finish_input = QLineEdit(self.finish)
        finish_layout.addWidget(self.finish_input)
        main_layout.addLayout(finish_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def accept(self):
        self.job_name = self.job_name_input.text().strip()

        # Get the ID of the currently checked radio button
        checked_button = self.edging_button_group.checkedButton()
        if checked_button:
            self.edging_flag = self.edging_button_group.id(checked_button)
        else:
            self.edging_flag = 0 # Fallback if for some reason no button is checked

        self.colour = self.colour_input.text().strip().upper()
        self.finish = self.finish_input.text().strip().upper()

        if not self.job_name:
            QMessageBox.warning(self, "Input Error", "Job Name cannot be empty.")
            return

        super().accept()


class EditEdgingPaintDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Edit {os.path.basename(file_path)}")
        self.setMinimumSize(600, 400)

        self.init_ui()
        self.load_file_content()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        info_label = QLabel(f"Edit the content of '{os.path.basename(self.file_path)}'. Each line should be 'KEY=VALUE'.")
        main_layout.addWidget(info_label)

        self.text_editor = QTextEdit()
        main_layout.addWidget(self.text_editor)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_file_content)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def load_file_content(self):
        if not os.path.exists(self.file_path):
            QMessageBox.information(self, "File Not Found", f"The file '{os.path.basename(self.file_path)}' does not exist. A new one will be created upon saving.")
            return

        try:
            with open(self.file_path, 'r') as f:
                self.text_editor.setText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", f"Could not load {os.path.basename(self.file_path)}: {e}")
            print(f"Error loading {self.file_path}: {e}")

    def save_file_content(self):
        content = self.text_editor.toPlainText()
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                f.write(content)
            QMessageBox.information(self, "Save Successful", f"{os.path.basename(self.file_path)} saved successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", f"Could not save {os.path.basename(self.file_path)}: {e}")
            print(f"Error saving {self.file_path}: {e}")


class JobHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Job History")
        self.setMinimumSize(800, 500)

        self.history_file_path = os.path.join(APP_BASE_DIR, JOB_HISTORY_FILE)

        self.init_ui()
        self.load_history_data()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        headers = ["Timestamp", "Job Name", "Edging Type", "Colour", "Finish"]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        main_layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self.clear_history_file)
        button_layout.addWidget(self.clear_history_button)

        button_layout.addStretch(1)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def load_history_data(self):
        self.table_widget.setRowCount(0)

        if not os.path.exists(self.history_file_path):
            print(f"Job history file not found at: {self.history_file_path}")
            return

        try:
            with open(self.history_file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                        row_position = self.table_widget.rowCount()
                        self.table_widget.insertRow(row_position)

                        self.table_widget.setItem(row_position, 0, QTableWidgetItem(entry.get("timestamp", "")))
                        self.table_widget.setItem(row_position, 1, QTableWidgetItem(entry.get("job_name", "")))
                        self.table_widget.setItem(row_position, 2, QTableWidgetItem(entry.get("edging_type", "")))
                        self.table_widget.setItem(row_position, 3, QTableWidgetItem(entry.get("colour", "")))
                        self.table_widget.setItem(row_position, 4, QTableWidgetItem(entry.get("finish", "")))
                    except json.JSONDecodeError:
                        print(f"Skipping malformed JSON line in history: {line_num + 1}")
                    except Exception as e:
                        print(f"Error processing history line {line_num + 1}: {e} - {line}")

            if self.table_widget.rowCount() == 0:
                 QMessageBox.information(self, "No History", "Job history file is empty or contains no valid entries.")

        except Exception as e:
            QMessageBox.critical(self, "History Error", f"Could not read job history file: {e}")
            print(f"Error reading job history file {self.history_file_path}: {e}")

    def clear_history_file(self):
        reply = QMessageBox.question(self, "Clear History",
                                     "Are you sure you want to clear ALL job history entries? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(self.history_file_path):
                    os.remove(self.history_file_path)
                    print(f"Job history file cleared: {self.history_file_path}")
                self.table_widget.setRowCount(0)
                QMessageBox.information(self, "History Cleared", "All job history entries have been removed.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history file: {e}")
                print(f"Error clearing history file {self.history_file_path}: {e}")