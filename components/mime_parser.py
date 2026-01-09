import os
from PyQt6.QtCore import QMimeData, QUrl

class DragAndDropParser:
    """
    Plugin-style helper to parse file paths from Drag and Drop MIME data.
    Handles:
    1. Standard OS File Dragging (Explorer/Finder)
    2. VS Code Tab Dragging (often text/plain)
    3. VS Code Tree View Dragging
    4. URL cleaning and validation
    """

    @staticmethod
    def parse_paths(mime_data: QMimeData) -> list[str]:
        paths = []

        # 1. Try Standard URLs (Qt handles most OS file managers here)
        if mime_data.hasUrls():
            # Iterate safely - fixes the IndexError if list is empty
            for url in mime_data.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path and os.path.exists(path):
                        paths.append(path)

        # 2. Try Text Fallback (VS Code Tabs, some Linux DMs)
        # If no URLs were found, check if it's a text drop containing a path
        if not paths and mime_data.hasText():
            text = mime_data.text().strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                path = DragAndDropParser._clean_text_path(line)
                if path and os.path.exists(path):
                    paths.append(path)
                    
        return paths

    @staticmethod
    def _clean_text_path(raw_text: str) -> str:
        """Cleans up raw text that might be a file URI or a messy path."""
        clean = raw_text.strip()
        
        # Remove URI prefixes
        if clean.startswith("file:///"): 
            clean = clean[8:]
        elif clean.startswith("file://"): 
            clean = clean[7:]
        
        # Handle Windows specific quirk: /C:/Users/... -> C:/Users/...
        if os.name == 'nt' and clean.startswith("/") and len(clean) > 2 and clean[2] == ":":
            clean = clean[1:]
            
        return clean