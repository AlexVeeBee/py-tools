import os
import importlib.metadata
import sys
from PyQt6.QtWidgets import QMessageBox

class DependencyChecker:
    @staticmethod
    def check(parent=None, req_file="requirements.txt"):
        """
        Checks for missing dependencies AND known conflicts (specifically Audio).
        """
        missing_packages = []
        conflicts = []

        # --- 1. CHECK FOR CONFLICTS (Audio) ---
        # The most common issue: User has both 'pyaudio' and 'pyaudiowpatch' installed.
        # This causes 'loopback' errors at runtime.
        try:
            has_standard = False
            has_patched = False
            
            try:
                importlib.metadata.distribution("pyaudio")
                has_standard = True
            except importlib.metadata.PackageNotFoundError:
                pass

            try:
                importlib.metadata.distribution("pyaudiowpatch")
                has_patched = True
            except importlib.metadata.PackageNotFoundError:
                pass

            # IF BOTH EXIST -> CONFLICT
            if has_standard and has_patched:
                conflicts.append(
                    "<b>CRITICAL AUDIO CONFLICT:</b><br>"
                    "You have both <i>pyaudio</i> and <i>pyaudiowpatch</i> installed.<br>"
                    "They overwrite each other and break Speaker capture.<br><br>"
                    "<b>SOLUTION:</b><br>"
                    "Run these commands in your terminal:<br>"
                    "<span style='color: #ff9800;'>pip uninstall -y pyaudio</span><br>"
                    "<span style='color: #ff9800;'>pip uninstall -y pyaudiowpatch</span><br>"
                    "<i>(Repeat until both say 'Skipping... not installed')</i><br>"
                    "<span style='color: #4caf50;'>pip install pyaudiowpatch</span>"
                )
        except Exception:
            pass

        # --- 2. CHECK MISSING PACKAGES ---
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    lines = f.readlines()

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'): continue

                    # Clean line (remove comments, versions)
                    clean_line = line.split(';')[0]
                    pkg_name = clean_line
                    for d in ['==', '>=', '<=', '>', '<', '~=', '[', ' ']:
                        pkg_name = pkg_name.split(d)[0]
                    pkg_name = pkg_name.strip()

                    try:
                        importlib.metadata.distribution(pkg_name)
                    except importlib.metadata.PackageNotFoundError:
                        missing_packages.append(line)

            except Exception as e:
                print(f"Error checking dependencies: {e}")

        # --- 3. SHOW POPUP IF NEEDED ---
        if missing_packages or conflicts:
            DependencyChecker._show_alert(parent, missing_packages, conflicts)
            return False

        return True

    @staticmethod
    def _show_alert(parent, missing, conflicts):
        msg_text = ""

        # Section 1: Conflicts (Highlighted Red/Warning)
        if conflicts:
            msg_text += "<h3>⚠️ SYSTEM CONFLICT DETECTED</h3>"
            for c in conflicts:
                msg_text += f"<p>{c}</p>"
            msg_text += "<hr>"

        # Section 2: Missing
        if missing:
            msg_text += "<h3>📦 MISSING REQUIREMENTS</h3>"
            msg_text += "The following packages are not installed:<br><br>"
            msg_text += "<pre style='color: #ff9800;'>" 
            msg_text += "<br>".join(missing[:8]) 
            if len(missing) > 8: msg_text += "<br>..."
            msg_text += "</pre>"
            msg_text += "<br>Please run: <b>pip install -r requirements.txt</b>"

        box = QMessageBox(parent)
        box.setWindowTitle("Environment Check")
        # Use RichText format
        box.setTextFormat(importlib.metadata.sys.modules['PyQt6.QtCore'].Qt.TextFormat.RichText) 
        box.setText(msg_text)
        box.setIcon(QMessageBox.Icon.Critical if conflicts else QMessageBox.Icon.Warning)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()