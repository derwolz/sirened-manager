# book_import/file_handlers.py

import csv
import json
import pandas as pd
import app_logger as logger

class FileHandler:
    """Handles reading and parsing different file types for book import"""
    
    def get_file_types(self, file_format):
        """Return appropriate file types based on format"""
        if file_format == "csv":
            return [("CSV files", "*.csv"), ("All files", "*.*")]
        elif file_format == "excel":
            return [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        elif file_format == "json":
            return [("JSON files", "*.json"), ("All files", "*.*")]
        return [("All files", "*.*")]
    
    def read_file_headers(self, file_path, file_format, skip_header=True):
        """Read file headers and first data row"""
        try:
            if file_format == "csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    first_row = next(reader, None)
            
            elif file_format == "excel":
                df = pd.read_excel(file_path)
                headers = df.columns.tolist()
                first_row = df.iloc[0].tolist() if not df.empty else None
            
            elif file_format == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        headers = list(data[0].keys())
                        first_row = list(data[0].values())
                    else:
                        headers = []
                        first_row = None
            
            else:
                headers = []
                first_row = None
                
            return headers, first_row
            
        except Exception as e:
            logger.log_error(f"Error reading file headers: {str(e)}")
            raise
    
    def read_file_data(self, file_path, file_format, skip_header=True):
        """Read all data from the file"""
        try:
            if file_format == "csv":
                df = pd.read_csv(file_path, header=0 if skip_header else None)
                return df.to_dict('records')
                
            elif file_format == "excel":
                df = pd.read_excel(file_path, header=0 if skip_header else None)
                return df.to_dict('records')
                
            elif file_format == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # If skip_header is True and it's a list, skip the first row
                if skip_header and isinstance(data, list) and len(data) > 0:
                    return data[1:]
                return data
                
            return []
            
        except Exception as e:
            logger.log_error(f"Error reading file data: {str(e)}")
            raise
