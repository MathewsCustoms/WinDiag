System Diagnostic Tool
This Python-based system diagnostic tool helps analyze and optimize the performance of a Windows computer. The tool comes in two versions:

Command-Line Interface (CLI) for direct terminal-based usage.
Graphical User Interface (GUI) for a user-friendly experience using PyQt.
Features
Common Features (CLI and GUI)
System Performance Checks:

CPU usage
Memory usage
Disk space
Temporary File Management:

Locate temporary files.
Clean temporary files to free up disk space.
Startup Application Management:

List startup applications.
Identify non-essential apps and recommend disabling them.
Top Processes:

View resource-hogging processes.
GUI-Specific Features
Interactive interface with buttons for each feature.
Startup apps listed with checkboxes for easy selection.
Results displayed in a scrollable text area.
Installation
Prerequisites
Python 3.9+
Install required Python packages:
psutil
PyQt5
Install Dependencies
Run the following command to install the required Python packages:

bash
Copy code
pip install psutil PyQt5
Usage
Command-Line Version
The command-line version provides diagnostics directly in the terminal. You can find and clean temporary files, check system health, and manage startup apps interactively.

Run the Script
bash
Copy code
python cli_diagnostic_tool.py
Features in CLI Version
System Health Checks:

CPU and memory usage displayed as percentages.
Disk space usage for each drive.
Temporary File Management:

Find temporary files in standard directories.
Clean them interactively based on user input.
Startup Applications:

Identify non-essential startup apps.
Recommend disabling apps interactively.
GUI Version
The GUI version provides an easy-to-use interface built with PyQt. All diagnostics can be run with a button click, and results are displayed in an interactive window.

Run the GUI
bash
Copy code
python gui_diagnostic_tool.py
Features in GUI Version
Button-Driven Actions:
Click buttons to perform system diagnostics like CPU check, memory check, or temporary file cleanup.
Startup Management:
View non-essential startup apps in a list with checkboxes.
Select apps to disable interactively.
Results Display:
Diagnostic results are displayed in a scrollable text area.
File Structure
bash
Copy code
.
├── cli_diagnostic_tool.py    # Command-Line Version
├── gui_diagnostic_tool.py    # GUI Version
├── README.md                 # Documentation
Future Improvements
Enhanced Startup Recommendations:
Use a dynamic database of critical apps to make smarter recommendations.
Real-Time Monitoring:
Add a dashboard to show real-time system metrics.
Cross-Platform Support:
Expand functionality to macOS and Linux.
Contributions
Contributions are welcome! If you'd like to improve the tool or add features, feel free to fork the repository and submit a pull request.

Steps to Contribute
Fork the repo.
Create a new branch:
bash
Copy code
git checkout -b feature-name
Commit changes and push:
bash
Copy code
git commit -m "Add feature"
git push origin feature-name
Submit a pull request.
License
This project is licensed under the MIT License.

