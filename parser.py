"""
Mudlogging Data Ingestion & Parsing Layer
Handles CSV, TXT, and Excel files from mudlogging rig sites.
Strips headers, metadata lines, converts values to float, cleans nulls.
"""

import pandas as pd
import numpy as np
import io
import os


def parse_mudlog_file(file_path_or_buffer):
    """
    Parses raw mudlogging log file.
    Expected standard columns: DEPTH, C1, C2, C3, IC4, NC4, IC5, NC5, TG
    """
    if isinstance(file_path_or_buffer, str):
        if not os.path.exists(file_path_or_buffer):
            raise FileNotFoundError(f"File not found: {file_path_or_buffer}")
        
        ext = os.path.splitext(file_path_or_buffer)[1].lower()
        if ext in ['.xlsx', '.xls']:
            df_raw = pd.read_excel(file_path_or_buffer)
        else:
            with open(file_path_or_buffer, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            header_idx = 0
            for i, line in enumerate(lines[:100]):
                line_upper = line.upper()
                if 'DEPTH' in line_upper or 'METRES' in line_upper or 'C1' in line_upper:
                    header_idx = i
                    break
            
            content = "".join(lines[header_idx:])
            df_raw = pd.read_csv(io.StringIO(content))
    else:
        df_raw = pd.read_csv(file_path_or_buffer)

    df_raw.columns = [str(col).strip().upper() for col in df_raw.columns]

    column_mapping = {
        'DEP': 'DEPTH', 'DEPTH_M': 'DEPTH', 'DEPTH_METRES': 'DEPTH',
        'CH4': 'C1', 'METHANE': 'C1',
        'C2H6': 'C2', 'ETHANE': 'C2',
        'C3H8': 'C3', 'PROPANE': 'C3',
        'I-C4': 'IC4', 'ISOBUTANE': 'IC4', 'I_C4': 'IC4',
        'N-C4': 'NC4', 'NORMALBUTANE': 'NC4', 'N_C4': 'NC4',
        'I-C5': 'IC5', 'ISOPENTANE': 'IC5', 'I_C5': 'IC5',
        'N-C5': 'NC5', 'NORMALPENTANE': 'NC5', 'N_C5': 'NC5',
        'TOTAL_GAS': 'TG', 'GAS': 'TG', 'TOT_GAS': 'TG'
    }
    
    df_raw = df_raw.rename(columns=column_mapping)

    required_cols = ['DEPTH', 'C1', 'C2', 'C3', 'IC4', 'NC4', 'IC5', 'NC5']
    for col in required_cols:
        if col not in df_raw.columns:
            df_raw[col] = 0.0

    valid_rows = []
    for idx, row in df_raw.iterrows():
        try:
            depth_val = float(row['DEPTH'])
            valid_rows.append(idx)
        except (ValueError, TypeError):
            continue

    df_clean = df_raw.loc[valid_rows].copy()

    cols_to_convert = ['DEPTH', 'C1', 'C2', 'C3', 'IC4', 'NC4', 'IC5', 'NC5']
    if 'TG' in df_clean.columns:
        cols_to_convert.append('TG')

    for col in cols_to_convert:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

    df_clean = df_clean.sort_values(by='DEPTH').reset_index(drop=True)
    return df_clean
