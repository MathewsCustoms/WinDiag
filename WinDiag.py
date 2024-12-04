import os
import shutil
import psutil
import subprocess
import winreg
import logging

# Configure logging
logging.basicConfig(filename='system_diagnosis.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# System Check Functions
def check_cpu_usage():
    usage = psutil.cpu_percent(interval=1)
    logging.info(f"CPU Usage: {usage}%")
    return f"CPU Usage: {usage}%"

def check_memory_usage():
    memory = psutil.virtual_memory()
    usage_details = f"Memory Usage: {memory.percent}% of {round(memory.total / (1024**3), 2)} GB"
    logging.info(usage_details)
    return usage_details

def check_disk_space():
    partitions = psutil.disk_partitions()
    disk_info = {}
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info[partition.device] = {
                "total": round(usage.total / (1024**3), 2),
                "used": round(usage.used / (1024**3), 2),
                "free": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            }
        except PermissionError as e:
            logging.warning(f"Permission denied for partition: {partition.device} - {e}")
    logging.info(f"Disk Information: {disk_info}")
    return disk_info

def find_temp_files():
    temp_dirs = [
        os.environ.get('TEMP', ''),
        os.path.expanduser('~\\AppData\\Local\\Temp'),
        "C:\\Windows\\Temp"
    ]
    temp_files = []
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            logging.warning(f"Temp directory not found: {temp_dir}")
            continue
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                temp_files.append(os.path.join(root, file))
    logging.info(f"Found {len(temp_files)} temporary files.")
    return temp_files

def clean_temp_files(files):
    failed_files = []
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            logging.error(f"Could not delete {file}: {e}")
            failed_files.append(file)
    if failed_files:
        logging.warning(f"Failed to delete {len(failed_files)} files.")
    logging.info(f"Successfully deleted {len(files) - len(failed_files)} files.")

def list_top_processes():
    processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                       key=lambda p: (p.info['cpu_percent'], p.info['memory_percent']),
                       reverse=True)[:5]
    result = []
    for proc in processes:
        try:
            result.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, "
                          f"CPU: {proc.info['cpu_percent']}%, Memory: {proc.info['memory_percent']}%")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    logging.info("Top processes: " + "; ".join(result))
    return result

# Startup Apps Functions
def get_startup_apps():
    startup_apps = []
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
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
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run") as key:
            i = 0
            while True:
                try:
                    app_name, app_path, _ = winreg.EnumValue(key, i)
                    startup_apps.append((app_name, app_path))
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass

    return startup_apps

def get_non_essential_startup_apps(apps):
    critical_apps = {
        "Windows Security Notification": True,
        "OneDrive": True,
        "Microsoft Teams": False,  # Example, adjust as needed
    }

    non_essential = []
    for app_name, app_path in apps:
        is_critical = critical_apps.get(app_name, None)
        if is_critical is None or not is_critical:
            non_essential.append((app_name, app_path))
    return non_essential

def display_and_choose_apps(apps):
    if not apps:
        print("No non-essential startup applications found.")
        return []

    print("\nNon-Essential Startup Applications:")
    for idx, (app_name, app_path) in enumerate(apps, 1):
        print(f"{idx}. {app_name} - {app_path}")

    print("\nEnter the numbers of the apps you want to disable (comma-separated):")
    user_input = input("Selection: ")
    try:
        selected_indices = [int(num.strip()) for num in user_input.split(",") if num.strip().isdigit()]
        selected_apps = [apps[idx - 1] for idx in selected_indices if 0 < idx <= len(apps)]
        return selected_apps
    except ValueError:
        print("Invalid input. No apps will be disabled.")
        return []

def disable_startup_apps(apps):
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
    ]
    
    for app_name, _ in apps:
        for hive, path in paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE) as key:
                    try:
                        winreg.DeleteValue(key, app_name)
                        print(f"Disabled startup app: {app_name}")
                        logging.info(f"Disabled startup app: {app_name}")
                        break
                    except FileNotFoundError:
                        continue
            except PermissionError as e:
                print(f"Permission denied while disabling {app_name}: {e}")
                logging.warning(f"Permission denied for {app_name}: {e}")

def main_startup_analysis():
    print("Checking Startup Applications...\n")
    
    apps = get_startup_apps()
    if not apps:
        print("No startup applications found.")
        return
    
    non_essential_apps = get_non_essential_startup_apps(apps)
    selected_apps = display_and_choose_apps(non_essential_apps)

    if selected_apps:
        print("\nDisabling selected apps...")
        disable_startup_apps(selected_apps)
        print("Selected apps have been disabled.")
    else:
        print("No apps were selected for disabling.")

# Main Function
def main():
    print("Starting System Diagnosis...\n")
    
    print(check_cpu_usage())
    print(check_memory_usage())
    
    disk_info = check_disk_space()
    for device, stats in disk_info.items():
        print(f"{device}: {stats['free']} GB free out of {stats['total']} GB ({stats['percent']}% used)")
    
    print("\nListing top resource-consuming processes:")
    top_processes = list_top_processes()
    for proc in top_processes:
        print(proc)
    
    temp_files = find_temp_files()
    print(f"\nTemporary Files Found: {len(temp_files)}")
    user_input = input("Do you want to clean these files? (yes/no): ")
    if user_input.lower() == 'yes':
        clean_temp_files(temp_files)
        print("Temporary files cleaned!")
    else:
        print("Skipped cleaning temporary files.")
    
    print("\nAnalyzing Startup Applications...")
    main_startup_analysis()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
        print("An error occurred. Please check the log file for details.")
