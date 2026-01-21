from components.styles import C_TEXT_MAIN, C_PRIMARY, C_BORDER

# Base CSS shared across all pages
BASE_STYLE = f"""
<style>
    body {{ font-family: sans-serif; color: {C_TEXT_MAIN}; line-height: 1.6; }}
    h1 {{ color: {C_PRIMARY}; margin-bottom: 10px; border-bottom: 2px solid {C_BORDER}; padding-bottom: 10px; }}
    h2 {{ color: #e0e0e0; margin-top: 25px; margin-bottom: 10px; }}
    h3 {{ color: {C_PRIMARY}; margin-top: 20px; font-size: 14px; }}
    code {{ background-color: #2b2b2b; padding: 2px 5px; border-radius: 4px; font-family: monospace; color: #e6db74; }}
    pre {{ background-color: #1e1e1e; padding: 15px; border-radius: 5px; color: #f8f8f2; border: 1px solid {C_BORDER}; }}
    li {{ margin-bottom: 8px; }}
    .key {{ background-color: #444; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
    .warn {{ color: #ff6b6b; font-weight: bold; }}
    .tip {{ color: #6bff81; font-weight: bold; }}
</style>
"""

def wrap_page(title, content):
    return f"""<!DOCTYPE html><html><head>{BASE_STYLE}</head><body><h1>{title}</h1>{content}</body></html>"""

# Define the Pages
PAGES = {
    "1. Introduction": wrap_page("Prompt Builder Guide", """
        <p>Welcome to the <b>Prompt Builder</b>.</p>
        <p>This tool helps you aggregate code files, folder structures, and specific instructions into a single context blob optimized for Large Language Models (LLMs).</p>
        <h2>Core Workflow</h2>
        <ol>
            <li><b>Add Blocks:</b> Use the buttons at the bottom to add Text, Files, or Folder Trees.</li>
            <li><b>Configure:</b> Drag & Drop files or select folders.</li>
            <li><b>Generate:</b> Click <b>GENERATE & COPY</b> to create the final prompt.</li>
        </ol>
    """),

    "2. Block Types": wrap_page("Block Types", """
        <h3>1. Message Block</h3>
        <ul>
            <li><b>Purpose:</b> Natural language instructions (e.g., "Fix this bug").</li>
            <li><b>Usage:</b> Just type your request in the text area.</li>
        </ul>

        <h3>2. File Block</h3>
        <ul>
            <li><b>Purpose:</b> Include specific file content.</li>
            <li><b>Action:</b> Drag a file from Explorer onto the block, or paste the path.</li>
            <li><b>Output:</b> Wraps content in Markdown code blocks (e.g., ```python ... ```).</li>
        </ul>

        <h3>3. Folder Tree Block</h3>
        <ul>
            <li><b>Purpose:</b> Visualizes directory structure.</li>
            <li><b>Context Injection:</b> Click <b>"Select Context Files..."</b> to checkmark specific files inside the tree. These specific files will be appended to the prompt.</li>
        </ul>
    """),

    "3. Managing Prompts": wrap_page("Saving & Loading", """
        <p>You can save your current configuration (blocks, paths, and text) to a database.</p>
        
        <h2>The Database</h2>
        <p>Prompts are stored in SQLite <code>.db</code> files. Use the selector at the top of the dialog to switch databases (e.g., specific to different projects).</p>

        <h2>Saving</h2>
        <ul>
            <li>Click <b>SAVE</b> in the main toolbar.</li>
            <li>Enter a unique name. If the name exists, you will be asked to overwrite.</li>
        </ul>

        <h2>Loading</h2>
        <ul>
            <li>Click <b>LOAD</b> to open the Manager.</li>
            <li><b>Single Click:</b> Previews the prompt structure on the right side.</li>
            <li><b>Double Click:</b> Immediately loads the prompt.</li>
        </ul>
    """),

    "4. Path Modes": wrap_page("Path Modes", """
        <p>The <b>Path Mode</b> dropdown controls how file headers are formatted in the final output.</p>
        
        <ul>
            <li><b>Name Only:</b> <code>main.py</code><br><i>Good for small contexts.</i></li>
            <li><b>Relative Path:</b> <code>src/utils/main.py</code><br><i>Best for most LLMs. Requires "Project Root" to be set.</i></li>
            <li><b>Full Path:</b> <code>C:/Projects/src/utils/main.py</code><br><i>Use for absolute clarity.</i></li>
        </ul>
        
        <p class="warn">Note: If Relative Path is selected but no Project Root is defined, it falls back to Full Path.</p>
    """),

    "5. Tips & Shortcuts": wrap_page("Tips & Tricks", """
        <h2>Shortcuts</h2>
        <ul>
            <li><span class="key">Drag & Drop</span>: Drag files from your OS onto text inputs to fill paths.</li>
            <li><span class="key">Enter</span>: In text inputs, confirms the path.</li>
        </ul>

        <h2>Ignore Patterns</h2>
        <p>Folder Trees automatically filter out noise. Common default patterns:</p>
        <pre>.git, __pycache__, node_modules, .idea, dist, build, .vscode</pre>
        
        <h2>Reordering</h2>
        <p>Grab the <span class="key">||</span> handle on the left side of any block to drag and reorder it within the stack.</p>
    """)
}