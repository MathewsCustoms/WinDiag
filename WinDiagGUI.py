import sys
import os
import psutil
import subprocess
import winreg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, 
    QHBoxLayout, QWidget, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import logging

# Configure logging
logging.basicConfig(filename='system_diagnosis.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SoftwareFetchThread(QThread):
    """Worker thread to fetch installed software."""
    software_fetched = pyqtSignal(list)  # Signal to send the fetched software list

    def run(self):
        """Fetch installed software in a separate thread."""
        software_list = []
        try:
            output = subprocess.check_output(
                ["powershell", "-Command", "Get-WmiObject -Class Win32_Product | Select-Object Name,Version,InstallDate"],
                universal_newlines=True
            )
            for line in output.splitlines():
                if line.strip() and "Name" not in line:
                    parts = line.split()
                    name = " ".join(parts[:-2])  # Assume last two fields are Version and InstallDate
                    version = parts[-2] if len(parts) >= 2 else "N/A"
                    install_date = parts[-1] if len(parts) >= 2 else "N/A"
                    software_list.append((name, version, install_date))
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to fetch installed software: {e}")
        self.software_fetched.emit(software_list)  # Emit signal with the fetched data


class SystemDiagnosticApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Diagnostic Tool")
        self.setGeometry(100, 100, 800, 600)
        self.center_window()  # Center the main window on the screen

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        # Add a label
        self.title_label = QLabel("System Diagnostic Tool")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # Create a text area for live stats
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.result_area)

        # Add buttons for actions
        self.button_layout = QHBoxLayout()
        self.temp_button = self.create_styled_button("Clean Temporary Files")
        self.process_button = self.create_styled_button("Manage Processes")
        self.startup_button = self.create_styled_button("Manage Startup Applications")
        self.software_button = self.create_styled_button("Manage Software")
        self.network_button = self.create_styled_button("Network Diagnostics")

        # Add buttons to layout
        self.button_layout.addWidget(self.temp_button)
        self.button_layout.addWidget(self.process_button)
        self.button_layout.addWidget(self.startup_button)
        self.button_layout.addWidget(self.software_button)
        self.button_layout.addWidget(self.network_button)
        self.layout.addLayout(self.button_layout)

        self.central_widget.setLayout(self.layout)

        # Connect buttons to functions
        self.temp_button.clicked.connect(self.clean_temp_files)
        self.process_button.clicked.connect(self.manage_processes)
        self.startup_button.clicked.connect(self.manage_startup_apps)
        self.software_button.clicked.connect(self.manage_software)
        self.network_button.clicked.connect(self.network_diagnostics)

        # Temporary file list
        self.temp_files = []

        # Set up a timer to update live stats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live_stats)
        self.timer.start(2000)  # Update every 2 seconds

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

    def center_window(self):
        """Center the main window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())

    def update_live_stats(self):
        """Update live system stats in the result area."""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage (all drives)
        disk_stats = ""
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_stats += (
                    f"{partition.device}: {usage.percent}% used of {round(usage.total / (1024**3), 2)} GB\n"
                )
            except PermissionError:
                continue
        
        # Temporary files count
        temp_dirs = [
            os.environ.get('TEMP', ''),
            os.path.expanduser('~\\AppData\\Local\\Temp'),
            "C:\\Windows\\Temp"
        ]
        temp_files_count = 0
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            for root, dirs, files in os.walk(temp_dir):
                temp_files_count += len(files)

        # Update text area
        self.result_area.setPlainText(
            f"CPU Usage: {cpu_usage}%\n"
            f"Memory Usage: {memory.percent}% of {round(memory.total / (1024**3), 2)} GB\n"
            f"Disk Usage:\n{disk_stats}"
            f"Temporary Files Count: {temp_files_count}\n"
        )

    def clean_temp_files(self):
        """Clean temporary files."""
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

    def manage_processes(self):
        """Display and manage running processes."""
        self.process_window = QWidget()
        self.process_window.setWindowTitle("Running Processes")
        self.center_child_window(self.process_window)  # Center the process window
        layout = QVBoxLayout()

        label = QLabel("Running Processes")
        layout.addWidget(label)

        self.process_list = QListWidget()
        processes = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])
        for proc in processes:
            try:
                text = f"PID: {proc.info['pid']}, Name: {proc.info['name']}, CPU: {proc.info['cpu_percent']}%, Memory: {proc.info['memory_percent']}%"
                item = QListWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.process_list.addItem(item)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        layout.addWidget(self.process_list)

        kill_button = self.create_styled_button("Kill Selected")
        kill_button.clicked.connect(self.kill_selected_processes)
        layout.addWidget(kill_button)

        self.process_window.setLayout(layout)
        self.process_window.resize(800, 600)
        self.process_window.show()

    def kill_selected_processes(self):
        """Kill selected processes."""
        for i in range(self.process_list.count()):
            item = self.process_list.item(i)
            if item.checkState() == Qt.Checked:
                pid = int(item.text().split(",")[0].split(":")[1].strip())
                try:
                    psutil.Process(pid).terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        QMessageBox.information(self, "Info", "Selected processes have been terminated.")

    def manage_startup_apps(self):
        """Display and manage startup applications."""
        startup_apps = self.get_startup_apps()

        self.startup_window = QWidget()
        self.startup_window.setWindowTitle("Startup Applications")
        self.center_child_window(self.startup_window)  # Center the startup window
        layout = QVBoxLayout()

        label = QLabel("Startup Applications")
        layout.addWidget(label)

        self.startup_list = QListWidget()
        for app_name, app_path in startup_apps:
            item = QListWidgetItem(f"{app_name} - {app_path}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.startup_list.addItem(item)
        layout.addWidget(self.startup_list)

        disable_button = self.create_styled_button("Disable Selected")
        disable_button.clicked.connect(self.disable_startup_apps)
        layout.addWidget(disable_button)

        self.startup_window.setLayout(layout)
        self.startup_window.resize(600, 400)
        self.startup_window.show()

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

    def disable_startup_apps(self):
        """Disable selected startup applications."""
        for i in range(self.startup_list.count()):
            item = self.startup_list.item(i)
            if item.checkState() == Qt.Checked:
                app_name = item.text().split(" - ")[0]
                self.delete_startup_app(app_name)

        QMessageBox.information(self, "Info", "Selected startup apps have been disabled.")

    def delete_startup_app(self, app_name):
        """Remove a startup application from the registry."""
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        ]
        for hive, path in paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE) as key:
                    try:
                        winreg.DeleteValue(key, app_name)
                        logging.info(f"Deleted startup app: {app_name}")
                        break
                    except FileNotFoundError:
                        continue
            except PermissionError as e:
                logging.error(f"Failed to delete {app_name}: {e}")

    def manage_software(self):
        """Display a window to manage installed software."""
        self.software_window = QWidget()
        self.software_window.setWindowTitle("Installed Software")
        self.center_child_window(self.software_window)  # Center the software window
        layout = QVBoxLayout()

        label = QLabel("Installed Software")
        layout.addWidget(label)

        self.software_table = QTableWidget()
        self.software_table.setColumnCount(3)
        self.software_table.setHorizontalHeaderLabels(["Name", "Version", "Install Date"])
        self.software_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.software_table)

        uninstall_button = self.create_styled_button("Uninstall Selected")
        uninstall_button.clicked.connect(self.uninstall_selected_software)
        layout.addWidget(uninstall_button)

        self.software_window.setLayout(layout)
        self.software_window.resize(800, 600)
        self.software_window.show()

        # Fetch installed software in a separate thread
        self.software_fetch_thread = SoftwareFetchThread()
        self.software_fetch_thread.software_fetched.connect(self.populate_software_table)
        self.software_fetch_thread.start()

    def populate_software_table(self, software):
        """Populate the software table with fetched data."""
        self.software_table.setRowCount(len(software))
        for row, (name, version, install_date) in enumerate(software):
            self.software_table.setItem(row, 0, QTableWidgetItem(name))
            self.software_table.setItem(row, 1, QTableWidgetItem(version))
            self.software_table.setItem(row, 2, QTableWidgetItem(install_date))

    def uninstall_selected_software(self):
        """Uninstall selected software."""
        selected_rows = self.software_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "No software selected for uninstallation.")
            return

        for row in selected_rows:
            name = self.software_table.item(row.row(), 0).text()
            try:
                subprocess.run(
                    ["powershell", "-Command", f"(Get-WmiObject -Class Win32_Product -Filter \"Name='{name}'\").Uninstall()"],
                    check=True
                )
                logging.info(f"Successfully uninstalled {name}.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to uninstall {name}: {e}")

        QMessageBox.information(self, "Success", "Selected software uninstalled successfully.")
        self.manage_software()  # Refresh the list

    def network_diagnostics(self):
        """Display active network connections."""
        self.network_window = QWidget()
        self.network_window.setWindowTitle("Network Diagnostics")
        self.center_child_window(self.network_window)  # Center the network window
        layout = QVBoxLayout()

        label = QLabel("Active Network Connections")
        layout.addWidget(label)

        self.network_table = QTableWidget()
        self.network_table.setColumnCount(4)
        self.network_table.setHorizontalHeaderLabels(["Local Address", "Remote Address", "Status", "PID"])
        self.network_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.network_table)

        connections = psutil.net_connections()
        self.network_table.setRowCount(len(connections))

        for row, conn in enumerate(connections):
            local_address = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
            remote_address = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
            status = conn.status
            pid = str(conn.pid) if conn.pid else "N/A"

            self.network_table.setItem(row, 0, QTableWidgetItem(local_address))
            self.network_table.setItem(row, 1, QTableWidgetItem(remote_address))
            self.network_table.setItem(row, 2, QTableWidgetItem(status))
            self.network_table.setItem(row, 3, QTableWidgetItem(pid))

        self.network_window.setLayout(layout)
        self.network_window.resize(800, 600)
        self.network_window.show()

    def center_child_window(self, window):
        """Center a child window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        window_rect = window.frameGeometry()
        window_rect.moveCenter(screen.center())
        window.move(window_rect.topLeft())


# Run the application
def main():
    app = QApplication(sys.argv)
    window = SystemDiagnosticApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
