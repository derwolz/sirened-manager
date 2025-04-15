import tkinter as tk
from tkinter import ttk

class SettingsTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Settings")
        
        self.setup_tab()
    
    def setup_tab(self):
        # Publisher checkbox
        publisher_check = ttk.Checkbutton(
            self.frame, 
            text="I am a publisher (enables author management)",
            variable=self.parent.is_publisher
        )
        publisher_check.pack(pady=20)
        
        # Instructions
        instructions = ttk.Label(
            self.frame,
            text="Instructions:\n\n" +
                 "1. Check 'I am a publisher' if you need to manage author data\n" +
                 "2. Fill in all required information in each tab\n" +
                 "3. For books, ensure every field is completed\n" +
                 "4. Each book must have at least 5 genre associations\n" +
                 "5. Each book must have EXACTLY the specified images\n" +
                 "6. When everything is complete, use the Export tab to save your data\n\n" +
                 "The system will package everything into a ZIP file with a checksum filename."
        )
        instructions.pack(pady=20)
