"""
Desktop shortcut installer.
Creates a desktop shortcut with radar/network icon pointing to the silent launcher.
"""
import os
import sys
from pathlib import Path

def install_desktop_shortcut():
    try:
        import win32com.client
    except ImportError:
        print("pywin32 not available, fallback to PowerShell")
        return False

    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop, "Internship Radar.lnk")
    
    project_dir = Path(__file__).resolve().parent.parent
    vbs_path = project_dir / "scripts" / "start_silent.vbs"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{str(vbs_path)}"'
    shortcut.WorkingDirectory = str(project_dir)
    shortcut.Description = "Internship Discovery Radar - GPU, AI & Systems"
    
    # Use network/radar icon from system DLL
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    icon_dll = os.path.join(system_root, "System32", "imageres.dll")
    if os.path.exists(icon_dll):
        shortcut.IconLocation = f"{icon_dll}, 175" # Radar / Globe icon in imageres.dll
    else:
        shortcut.IconLocation = f"{os.path.join(system_root, 'System32', 'shell32.dll')}, 14"

    shortcut.Save()
    print(f"[SUCCESS] Desktop shortcut created at: {shortcut_path}")
    return True

if __name__ == "__main__":
    install_desktop_shortcut()
