"""
Configures Internship Radar background runner to automatically start on Windows login.
"""
import os
from pathlib import Path
import win32com.client

def setup_startup_shortcut(enable: bool = True):
    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("[ERROR] APPDATA environment variable not found.")
        return

    startup_folder = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_folder, "Internship Radar Scheduler.lnk")

    if not enable:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"[INFO] Removed startup shortcut: {shortcut_path}")
        return

    project_dir = Path(__file__).resolve().parent.parent
    vbs_path = project_dir / "scripts" / "start_silent.vbs"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{str(vbs_path)}"'
    shortcut.WorkingDirectory = str(project_dir)
    shortcut.Description = "Internship Radar Background Engine"
    shortcut.Save()
    print(f"[SUCCESS] Configured Windows Startup shortcut at: {shortcut_path}")

if __name__ == "__main__":
    setup_startup_shortcut(True)
