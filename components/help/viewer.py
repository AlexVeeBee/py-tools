from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from components.styles import C_BG_MAIN, C_TEXT_MAIN, C_PRIMARY, C_BORDER

HELP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: sans-serif; color: {C_TEXT_MAIN}; }}
    h1 {{ color: {C_PRIMARY}; margin-bottom: 10px; }}
    h2 {{ color: {C_PRIMARY}; margin-top: 20px; border-bottom: 1px solid {C_BORDER}; padding-bottom: 5px; }}
    h3 {{ color: #a0a0a0; margin-top: 15px; }}
    code {{ background-color: #2b2b2b; padding: 2px 4px; border-radius: 3px; font-family: monospace; color: #e6db74; }}
    pre {{ background-color: #2b2b2b; padding: 10px; border-radius: 5px; color: #f8f8f2; }}
    li {{ margin-bottom: 5px; }}
    .warning {{ color: #ff5555; font-weight: bold; }}
</style>
</head>
<body>

<h1>Prompt Builder Guide</h1>
<p>The Prompt Builder helps you aggregate code files, folder structures, and instructions into a single context blob for Large Language Models (LLMs).</p>

<h2>Block Types</h2>

<h3>1. Message Block</h3>
<ul>
    <li><b>Purpose:</b> Natural language instructions.</li>
    <li><b>Example:</b> "Refactor the code below to use async/await."</li>
</ul>

<h3>2. File Block</h3>
<ul>
    <li><b>Purpose:</b> Include the content of a specific file.</li>
    <li><b>Behavior:</b> Automatically detects the file extension and wraps content in markdown code blocks.</li>
</ul>

<h3>3. Folder Tree Block</h3>
<ul>
    <li><b>Purpose:</b> Visualize directory structure and inject specific context files.</li>
    <li><b>Injection:</b> Click the <b>"Select Context Files..."</b> button on the block to check specific files inside the folder. These are appended after the tree.</li>
</ul>

<h2>Path Modes</h2>
<p>The "Mode" dropdown determines how file headers appear:</p>
<ul>
    <li><b>Name Only:</b> <code>main.py</code></li>
    <li><b>Relative Path:</b> <code>src/utils/main.py</code> (Requires "Project Root" to be set).</li>
    <li><b>Full Path:</b> <code>C:/Projects/src/utils/main.py</code></li>
</ul>

<h2>Ignore Patterns</h2>
<p>Used to filter noise from Folder Trees. Default patterns include:</p>
<pre>.git, node_modules, __pycache__, .idea, .vscode, dist, build</pre>

<h2>Tips & Shortcuts</h2>
<ul>
    <li><b>Drag & Drop:</b> Drag a file from your OS explorer onto a block's text input to set its path.</li>
    <li><b>Reorder:</b> Drag the <code>||</code> handle on the left of a block to move it.</li>
    <li><b>Copy:</b> Use "GENERATE & COPY" to immediately get the text into your clipboard.</li>
</ul>

</body>
</html>
"""

class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"background-color: {C_BG_MAIN}; border: none;")
        self.browser.setHtml(HELP_HTML)
        
        layout.addWidget(self.browser)