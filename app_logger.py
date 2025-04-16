"""
app_logger.py - Standalone logger module for Book Catalog Formatter application
This module provides global logging functions that can be used from any part of the application
"""

import datetime
import sys
import tkinter as tk
from tkinter import ttk

# Global variables to hold references to log widgets
debug_text = None
warning_text = None
error_text = None
debug_notebook = None
debug_enabled = True
root = None

# Log queues for when UI is not available yet
debug_queue = []
warning_queue = []
error_queue = []

def initialize(tk_root, debug_text_widget, error_text_widget,warning_text_widget, debug_notebook_widget):
    """Initialize the logger with UI components"""
    global debug_text, error_text, debug_notebook, root, warning_text
    
    debug_text = debug_text_widget
    error_text = error_text_widget

    warning_text = warning_text_widget

    debug_notebook = debug_notebook_widget
    root = tk_root
    
    # Process any queued messages
    for message in debug_queue:
        log_debug(message)
    debug_queue.clear()
    
    for message in error_queue:
        log_error(message)
    error_queue.clear()


def set_debug_enabled(enabled):
    """Enable or disable debug logging"""
    global debug_enabled
    debug_enabled = enabled

def log_debug(message):
    """Log a debug message to the debug text widget and console"""
    if not debug_enabled:
        return
        
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Always print to console
    print(f"[DEBUG] {formatted_message}")
    sys.stdout.flush()  # Force flush stdout to ensure message appears
    
    # If UI not initialized yet, queue the message
    if debug_text is None:
        debug_queue.append(message)
        return
    
    # Update the UI
    try:
        debug_text.configure(state="normal")
        debug_text.insert(tk.END, formatted_message + "\n")
        debug_text.see(tk.END)  # Scroll to the bottom
        debug_text.configure(state="disabled")
        
        # Process events to update UI
        if root:
            root.update_idletasks()
    except Exception as e:
        print(f"[ERROR] Failed to update debug log UI: {str(e)}")
        sys.stdout.flush()

def log_warning(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(f"[WARNING] {formatted_message}")
    sys.stdout.flush()
    if error_text is None:
        warning_queue.append(message)
        return
    try:
        warning_text.configure(state="normal")
        warning_text.insert(tk.END, formatted_message + "\n")
        warning_text.see(tk.END)
        warning_text.configure(state="disabled")

        if debug_notebook:
                debug_notebook.select(1)
        if root:
            root.update_idletasks()
    except Exception as E:
        print(f"[ERROR] FAILED TO update warning log UI: {str(e)}")
        sys.stdout.flush()

def log_error(message):
    """Log an error message to the error text widget and console"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Always print to console
    print(f"[ERROR] {formatted_message}")
    sys.stdout.flush()  # Force flush stdout to ensure message appears
    
    # If UI not initialized yet, queue the message
    if error_text is None:
        error_queue.append(message)
        return
    
    # Update the UI
    try:
        error_text.configure(state="normal")
        error_text.insert(tk.END, formatted_message + "\n")
        error_text.see(tk.END)  # Scroll to the bottom
        error_text.configure(state="disabled")
        
        # Switch to error tab
        if debug_notebook:
            debug_notebook.select(1)
            
        # Process events to update UI
        if root:
            root.update_idletasks()
    except Exception as e:
        print(f"[ERROR] Failed to update error log UI: {str(e)}")
        sys.stdout.flush()

def clear_debug_log():
    """Clear the debug log"""
    if debug_text:
        debug_text.configure(state="normal")
        debug_text.delete(1.0, tk.END)
        debug_text.configure(state="disabled")

def clear_warning_log():
    """Clear the warning log"""
    if warning_text:
        warning_text.configure(state="normal")
        warning_text.delete(1.0, tk.END)
        warning_text.configure(state="disabled")

def clear_error_log():
    """Clear the error log"""
    if error_text:
        error_text.configure(state="normal")
        error_text.delete(1.0, tk.END)
        error_text.configure(state="disabled")
