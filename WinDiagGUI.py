import sys
import os
import psutil
import winreg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, 
    QHBoxLayout, QWidget, QLabel, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
import logging

# Configure logging
logging.basicConfig(filename='system_diagnosis.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SystemDiagnosticApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Diagnostic Tool")
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        # Add a label
        self.title_label = QLabel("System Diagnostic Tool")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # Create two columns of buttons
        self.button_layout = QHBoxLayout()
        self.left_column = QVBoxLayout()
        self.right_column = QVBoxLayout()

        # Buttons for actions
        self.cpu_button = self.create_styled_button("Check CPU Usage")
        self.memory_button = self.create_styled_button("Check Memory Usage")
        self.disk_button = self.create_styled_button("Check Disk Space")
        self.temp_button = self.create_styled_button("Find Temporary Files")
        self.clear_temp_button = self.create_styled_button("Clean Temporary Files")
        self.startup_button = self.create_styled_button("Manage Startup Applications")
        self.process_button = self.create_styled_button("Manage Processes")  # Process Management Button

        # Add buttons to respective columns
        self.left_column.addWidget(self.cpu_button)
        self.left_column.addWidget(self.memory_button)
        self.left_column.addWidget(self.disk_button)
        self.left_column.addWidget(self.process_button)  # Add Process Management button here

        self.right_column.addWidget(self.temp_button)
        self.right_column.addWidget(self.startup_button)
        self.right_column.addWidget(self.clear_temp_button)

        # Add columns to the layout
        self.button_layout.addLayout(self.left_column)
        self.button_layout.addLayout(self.right_column)
        self.layout.addLayout(self.button_layout)

        # Text area to display results
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.result_area)

        self.central_widget.setLayout(self.layout)

        # Connect buttons to functions
        self.cpu_button.clicked.connect(self.check_cpu_usage)
        self.memory_button.clicked.connect(self.check_memory_usage)
        self.disk_button.clicked.connect(self.check_disk_space)
        self.temp_button.clicked.connect(self.find_temp_files)
        self.clear_temp_button.clicked.connect(self.clean_temp_files)
        self.startup_button.clicked.connect(self.manage_startup_apps)  # Correctly connected to manage_startup_apps
        self.process_button.clicked.connect(self.manage_processes)  # Correctly connected to manage_processes

        # Temporary file list
        self.temp_files = []

    def create_styled_button(self, text):
        """Create a styled button with rounded edges and blue color."""
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #003f7f;
            }
        """)
        return button

    # System diagnostic functions
    def check_cpu_usage(self):
        usage = psutil.cpu_percent(interval=1)
        self.result_area.append(f"CPU Usage: {usage}%")
        logging.info(f"CPU Usage: {usage}%")

    def check_memory_usage(self):
        memory = psutil.virtual_memory()
        result = f"Memory Usage: {memory.percent}% of {round(memory.total / (1024**3), 2)} GB"
        self.result_area.append(result)
        logging.info(result)

    def check_disk_space(self):
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                result = (
                    f"Drive {partition.device}: "
                    f"{usage.free // (1024**3)} GB free out of {usage.total // (1024**3)} GB "
                    f"({usage.percent}% used)"
                )
                self.result_area.append(result)
                logging.info(result)
            except PermissionError as e:
                logging.warning(f"Permission denied for partition: {partition.device}")

    def find_temp_files(self):
        temp_dirs = [
            os.environ.get('TEMP', ''),
            os.path.expanduser('~\\AppData\\Local\\Temp'),
            "C:\\Windows\\Temp"
        ]
        self.temp_files = []
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    self.temp_files.append(os.path.join(root, file))
        self.result_area.append(f"Found {len(self.temp_files)} temporary files.")
        logging.info(f"Found {len(self.temp_files)} temporary files.")

    def clean_temp_files(self):
        if not self.temp_files:
            QMessageBox.information(self, "Info", "No temporary files found to clean.")
            return

        failed_files = []
        for file in self.temp_files:
            try:
                os.remove(file)
            except Exception as e:
                logging.error(f"Could not delete {file}: {e}")
                failed_files.append(file)

        success_count = len(self.temp_files) - len(failed_files)
        QMessageBox.information(
            self, "Cleanup Complete", 
            f"Successfully cleaned {success_count} files. Failed to clean {len(failed_files)} files."
        )
        logging.info(f"Successfully deleted {success_count} files. Failed: {len(failed_files)}")
        self.temp_files = []

    def manage_startup_apps(self):
        """Display a window to manage startup applications."""
        startup_apps = self.get_startup_apps()
        non_essential_apps = self.get_non_essential_startup_apps(startup_apps)

        # Create a new window for startup management
        self.startup_window = QWidget()
        self.startup_window.setWindowTitle("Manage Startup Applications")
        layout = QVBoxLayout()

        # Add label
        label = QLabel("Non-Essential Startup Applications:")
        layout.addWidget(label)

        # Startup app list
        self.startup_list = QListWidget()
        for app_name, app_path in non_essential_apps:
            item = QListWidgetItem(f"{app_name} - {app_path}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.startup_list.addItem(item)
        layout.addWidget(self.startup_list)

        # Disable Selected button
        disable_button = self.create_styled_button("Disable Selected")
        disable_button.clicked.connect(self.disable_selected_startup_apps)
        layout.addWidget(disable_button)

        self.startup_window.setLayout(layout)
        self.startup_window.resize(600, 400)
        self.startup_window.show()

    def disable_selected_startup_apps(self):
        """Disable selected startup applications."""
        selected_apps = []
        for i in range(self.startup_list.count()):
            item = self.startup_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_apps.append(item.text().split(" - ")[0])

        if not selected_apps:
            QMessageBox.information(self, "Info", "No apps selected for disabling.")
            return

        for app_name in selected_apps:
            self.disable_startup_app(app_name)

        QMessageBox.information(self, "Success", f"Disabled {len(selected_apps)} startup apps.")
        self.startup_window.close()

    def disable_startup_app(self, app_name):
        """Disable a single startup application."""
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        ]
        for hive, path in paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE) as key:
                    try:
                        winreg.DeleteValue(key, app_name)
                        logging.info(f"Disabled startup app: {app_name}")
                        break
                    except FileNotFoundError:
                        continue
            except PermissionError as e:
                logging.error(f"Failed to disable {app_name}: {e}")

    def get_startup_apps(self):
        """Retrieve startup applications."""
        startup_apps = []
        paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
        ]
        for path in paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    i = 0
                    while True:
                        try:
                            app_name, app_path, _ = winreg.EnumValue(key, i)
                            startup_apps.append((app_name, app_path))
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                continue
        return startup_apps

    def get_non_essential_startup_apps(self, apps):
        """Filter non-essential startup applications."""
        critical_apps = {
            "Windows Security Notification": True,
            "OneDrive": True,
            "Microsoft Teams": False
        }
        return [
            (app_name, app_path) 
            for app_name, app_path in apps 
            if not critical_apps.get(app_name, False)
        ]

    # Process Management
    def manage_processes(self):
        """Display a window to manage running processes."""
        self.process_window = QWidget()
        self.process_window.setWindowTitle("Manage Running Processes")
        layout = QVBoxLayout()

        # Add label
        label = QLabel("Select processes to terminate:")
        layout.addWidget(label)

        # Process list
        self.process_list = QListWidget()
        self.update_process_list()
        layout.addWidget(self.process_list)

        # Kill Selected button
        kill_button = QPushButton("Kill Selected")
        kill_button.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
        """)
        kill_button.clicked.connect(self.kill_selected_processes)
        layout.addWidget(kill_button)

        self.process_window.setLayout(layout)
        self.process_window.resize(600, 400)
        self.process_window.show()

    def update_process_list(self):
        """Fetch and display running processes sorted by CPU or memory usage."""
        self.process_list.clear()

        # Fetch processes
        processes = sorted(
            psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
            key=lambda p: (p.info['cpu_percent'], p.info['memory_percent']),
            reverse=True
        )

        # Populate list
        for proc in processes:
            try:
                item_text = (
                    f"PID: {proc.info['pid']}, "
                    f"Name: {proc.info['name']}, "
                    f"CPU: {proc.info['cpu_percent']}%, "
                    f"Memory: {proc.info['memory_percent']}%"
                )
                item = QListWidgetItem(item_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.process_list.addItem(item)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def kill_selected_processes(self):
        """Terminate selected processes."""
        selected_items = []
        for i in range(self.process_list.count()):
            item = self.process_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_items.append(item.text())

        if not selected_items:
            QMessageBox.information(self, "Info", "No processes selected for termination.")
            return

        failed = []
        for item_text in selected_items:
            pid = int(item_text.split(",")[0].split(":")[1].strip())  # Extract PID
            try:
                process = psutil.Process(pid)
                process.terminate()
                self.process_list.takeItem(self.process_list.row(item))
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logging.error(f"Failed to terminate process {pid}: {e}")
                failed.append(pid)

        if failed:
            QMessageBox.warning(self, "Warning", f"Failed to terminate {len(failed)} processes.")
        else:
            QMessageBox.information(self, "Success", "Selected processes terminated successfully.")

        self.update_process_list()


# Run the application
def main():
    app = QApplication(sys.argv)
    window = SystemDiagnosticApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
