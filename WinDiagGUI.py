import sys
import os
import psutil
import winreg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, 
    QWidget, QLabel, QListWidget, QListWidgetItem, QMessageBox, QCheckBox
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

        # Buttons for actions
        self.cpu_button = QPushButton("Check CPU Usage")
        self.memory_button = QPushButton("Check Memory Usage")
        self.disk_button = QPushButton("Check Disk Space")
        self.temp_button = QPushButton("Find Temporary Files")
        self.startup_button = QPushButton("Manage Startup Applications")
        self.clear_temp_button = QPushButton("Clean Temporary Files")

        # Text area to display results
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)

        # Add buttons and result area to layout
        self.layout.addWidget(QLabel("System Diagnostic Tool"))
        self.layout.addWidget(self.cpu_button)
        self.layout.addWidget(self.memory_button)
        self.layout.addWidget(self.disk_button)
        self.layout.addWidget(self.temp_button)
        self.layout.addWidget(self.startup_button)
        self.layout.addWidget(self.clear_temp_button)
        self.layout.addWidget(self.result_area)

        self.central_widget.setLayout(self.layout)

        # Connect buttons to functions
        self.cpu_button.clicked.connect(self.check_cpu_usage)
        self.memory_button.clicked.connect(self.check_memory_usage)
        self.disk_button.clicked.connect(self.check_disk_space)
        self.temp_button.clicked.connect(self.find_temp_files)
        self.startup_button.clicked.connect(self.manage_startup_apps)
        self.clear_temp_button.clicked.connect(self.clean_temp_files)

        # Temporary file list
        self.temp_files = []

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
        startup_apps = self.get_startup_apps()
        non_essential_apps = self.get_non_essential_startup_apps(startup_apps)

        # Display the apps in a list with checkboxes
        self.startup_window = QWidget()
        self.startup_window.setWindowTitle("Manage Startup Applications")
        layout = QVBoxLayout()

        label = QLabel("Non-Essential Startup Applications")
        layout.addWidget(label)

        self.app_list = QListWidget()
        for app_name, app_path in non_essential_apps:
            item = QListWidgetItem(f"{app_name} - {app_path}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.app_list.addItem(item)

        layout.addWidget(self.app_list)
        disable_button = QPushButton("Disable Selected")
        disable_button.clicked.connect(self.disable_selected_startup_apps)
        layout.addWidget(disable_button)

        self.startup_window.setLayout(layout)
        self.startup_window.resize(600, 400)
        self.startup_window.show()

    def disable_selected_startup_apps(self):
        selected_apps = []
        for i in range(self.app_list.count()):
            item = self.app_list.item(i)
            if item.checkState() == Qt.Checked:
                app_name = item.text().split(" - ")[0]
                selected_apps.append(app_name)

        if not selected_apps:
            QMessageBox.information(self, "Info", "No apps selected for disabling.")
            return

        self.disable_startup_apps(selected_apps)
        QMessageBox.information(self, "Info", f"Disabled {len(selected_apps)} startup apps.")
        self.startup_window.close()

    # Startup app utility functions
    def get_startup_apps(self):
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

    def disable_startup_apps(self, apps):
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        ]
        for app_name in apps:
            for hive, path in paths:
                try:
                    with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE) as key:
                        try:
                            winreg.DeleteValue(key, app_name)
                            logging.info(f"Disabled startup app: {app_name}")
                        except FileNotFoundError:
                            continue
                except PermissionError as e:
                    logging.warning(f"Permission denied for {app_name}: {e}")


# Run the application
def main():
    app = QApplication(sys.argv)
    window = SystemDiagnosticApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
