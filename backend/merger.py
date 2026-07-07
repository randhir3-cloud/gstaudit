import io
import re
import copy as _copy_module
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import PatternFill, Font as OxlFont

MONTH_MAP = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
}

FULL_MONTH_MAP = {
    '01': 'January',  '02': 'February', '03': 'March',    '04': 'April',
    '05': 'May',      '06': 'June',     '07': 'July',     '08': 'August',
    '09': 'September','10': 'October',  '11': 'November', '12': 'December',
}

GSTR1_SKIP_SHEETS = {'read me'}
GSTR1_HEADER_ROW = 3

README_TAX_PERIOD_ROW = 4
README_ARN_ROW = 8
README_ARN_DATE_ROW = 9
README_VALUE_COL = 2

# ---- Financial-year helpers ----
def fy_sort_key(mm: str, yyyy: str) -> int:
    mm_int, yyyy_int = int(mm), int(yyyy)
    if mm_int >= 4:
        return yyyy_int * 100 + (mm_int - 3)
    else:
        return (yyyy_int - 1) * 100 + (mm_int + 9)

def fy_key_to_label(key: int) -> str:
    idx = key % 100
    fy_start_yr = key // 100
    if idx <= 9:
        cal_month = idx + 3
        cal_year = fy_start_yr
    else:
        cal_month = idx - 9
        cal_year = fy_start_yr + 1
    return f"{FULL_MONTH_MAP.get(f'{cal_month:02d}', str(cal_month))} {cal_year}"

def next_fy_key(key: int) -> int:
    idx = key % 100
    fy_year = key // 100
    if idx < 12:
        return fy_year * 100 + (idx + 1)
    return (fy_year + 1) * 100 + 1

def file_fy_key(filename: str) -> int:
    m = re.search(r'_(\d{2})(\d{4})_', filename)
    if m:
        return fy_sort_key(m.group(1), m.group(2))
    return 999999

def extract_period(filename: str) -> str:
    m = re.search(r'_(\d{2})(\d{4})_', filename)
    if m:
        mm, yyyy = m.group(1), m.group(2)
        return f"{MONTH_MAP.get(mm, mm)}-{yyyy}"
    # fallback
    name_without_ext = filename.split('.')[0]
    return name_without_ext

def find_missing_months(filenames: List[str]) -> List[str]:
    present = set()
    for fname in filenames:
        m = re.search(r'_(\d{2})(\d{4})_', fname)
        if m:
            present.add(fy_sort_key(m.group(1), m.group(2)))

    if len(present) < 2:
        return []

    min_key = min(present)
    max_key = max(present)
    missing = []
    cur = next_fy_key(min_key)
    while cur < max_key:
        if cur not in present:
            missing.append(fy_key_to_label(cur))
        cur = next_fy_key(cur)
    return missing

# ---- Style helpers ----
def copy_cell_style(src, dst):
    if src is None or not src.has_style:
        return
    dst.font          = _copy_module.copy(src.font)
    dst.fill          = _copy_module.copy(src.fill)
    dst.border        = _copy_module.copy(src.border)
    dst.alignment     = _copy_module.copy(src.alignment)
    dst.number_format = src.number_format
    dst.protection    = _copy_module.copy(src.protection)

def apply_data_style(src_hdr, dst):
    if src_hdr is not None and src_hdr.has_style:
        dst.number_format = src_hdr.number_format
    dst.fill = PatternFill(fill_type=None)
    dst.font = OxlFont(color='FF000000')

def safe_value(val):
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.bool_):
        return bool(val)
    return val

# ---- E-Way Bill Merger ----
def merge_eway_bills(files: List[Tuple[str, bytes]]) -> io.BytesIO:
    """
    files: List of tuples containing (filename, file_content_bytes)
    """
    if not files:
        raise ValueError("No files provided for merging.")

    all_dfs = []
    for filename, content in files:
        try:
            # Handle .xls files that might actually be HTML tables
            if filename.lower().endswith('.xls'):
                header = content[:500].lower()
                if b'<html' in header or b'<!doctype html' in header or b'<style' in header:
                    tables = pd.read_html(io.BytesIO(content))
                    if not tables:
                        raise ValueError(f"No tables found in HTML-xls file {filename}")
                    
                    # Convert to xlsx DataFrame
                    df_temp = tables[0]
                    # We save to BytesIO to simulate writing and reading back to make it uniform
                    xlsx_buffer = io.BytesIO()
                    df_temp.to_excel(xlsx_buffer, index=False, engine='openpyxl')
                    xlsx_buffer.seek(0)
                    xls = pd.ExcelFile(xlsx_buffer, engine='openpyxl')
                else:
                    xls = pd.ExcelFile(io.BytesIO(content), engine='xlrd')
            else:
                xls = pd.ExcelFile(io.BytesIO(content), engine='openpyxl')

            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name, engine='openpyxl')
                except Exception:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                df['Source_File']  = filename
                df['Source_Sheet'] = sheet_name
                all_dfs.append(df)
        except Exception as e:
            raise ValueError(f"Error processing {filename}: {str(e)}")

    if not all_dfs:
        raise ValueError("No data found to merge.")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    output_buffer = io.BytesIO()
    combined_df.to_excel(output_buffer, index=False, engine='openpyxl')
    output_buffer.seek(0)
    return output_buffer

# ---- GSTR-1 Merger ----
def merge_gstr1_files(files: List[Tuple[str, bytes]]) -> Tuple[io.BytesIO, str, List[str]]:
    """
    files: List of tuples containing (filename, file_content_bytes)
    Returns: (output_bytes_io, auto_name, missing_months_list)
    """
    if not files:
        raise ValueError("No files provided for merging.")

    filenames = [f[0] for f in files]
    missing = find_missing_months(filenames)

    # Sort files in Financial Year order (April -> March)
    sorted_files = sorted(files, key=lambda f: file_fy_key(f[0]))

    # Step 1: Determine Tax Period range from sorted filenames
    period_keys = []
    for filename, _ in sorted_files:
        m = re.search(r'_(\d{2})(\d{4})_', filename)
        if m:
            mm, yyyy = m.group(1), m.group(2)
            period_keys.append(
                (int(yyyy) * 100 + int(mm), FULL_MONTH_MAP.get(mm, mm), yyyy)
            )

    if period_keys:
        period_keys.sort()
        first_label = f"{period_keys[0][1]} {period_keys[0][2]}"
        last_label  = f"{period_keys[-1][1]} {period_keys[-1][2]}"
        tax_period_text = (
            first_label if first_label == last_label
            else f"{first_label} to {last_label}"
        )
    else:
        tax_period_text = "Full Period"

    # Step 2: Collect data rows per sheet from ALL sorted files
    sheet_data: Dict[str, List[pd.DataFrame]] = {}

    for filename, content in sorted_files:
        period = extract_period(filename)
        try:
            xls = pd.ExcelFile(io.BytesIO(content), engine='openpyxl')
        except Exception:
            xls = pd.ExcelFile(io.BytesIO(content))

        for sheet_name in xls.sheet_names:
            if sheet_name.strip().lower() in GSTR1_SKIP_SHEETS:
                continue

            try:
                df = pd.read_excel(
                    xls, sheet_name=sheet_name,
                    header=GSTR1_HEADER_ROW, engine='openpyxl'
                )
            except Exception:
                df = pd.read_excel(
                    xls, sheet_name=sheet_name,
                    header=GSTR1_HEADER_ROW
                )

            df.dropna(how='all', inplace=True)
            if df.empty:
                continue

            df.insert(0, 'Source_Period', period)
            if sheet_name not in sheet_data:
                sheet_data[sheet_name] = []
            sheet_data[sheet_name].append(df)

    # Step 3: Load the first sorted file as the formatting TEMPLATE
    first_filename, first_content = sorted_files[0]
    wb = openpyxl.load_workbook(io.BytesIO(first_content))

    # 1-based Excel row indices
    HEADER_ROW = GSTR1_HEADER_ROW + 1
    DATA_START = HEADER_ROW + 1

    # Step 3b: Auto-generate output filename from Read me metadata
    readme_ws_name = next(
        (sn for sn in wb.sheetnames if sn.strip().lower() == 'read me'),
        None
    )
    val_col = README_VALUE_COL + 1

    if readme_ws_name:
        ws_rm_meta = wb[readme_ws_name]
        gstin_val  = ws_rm_meta.cell(row=6, column=val_col).value or ''
        fy_val     = ws_rm_meta.cell(row=4, column=val_col).value or ''
        safe_gstin = re.sub(r'[\\/:*?"<>|]', '_', str(gstin_val).strip())
        safe_fy    = re.sub(r'[\\/:*?"<>|]', '_', str(fy_val).strip())
        auto_name  = f"GSTR1_{safe_gstin}_{safe_fy}_Merged.xlsx"
    else:
        auto_name = "GSTR1_Merged.xlsx"

    # Step 4: Patch "Read me" Tax Period / ARN directly in the template worksheet
    if readme_ws_name:
        ws_rm = wb[readme_ws_name]
        ws_rm.cell(
            row=README_TAX_PERIOD_ROW + 1, column=val_col
        ).value = tax_period_text
        ws_rm.cell(row=README_ARN_ROW      + 1, column=val_col).value = ''
        ws_rm.cell(row=README_ARN_DATE_ROW + 1, column=val_col).value = ''

    # Step 5: For every sheet in the template workbook
    for sheet_name in wb.sheetnames:
        if sheet_name.strip().lower() in GSTR1_SKIP_SHEETS:
            continue

        if sheet_name not in sheet_data:
            continue

        ws = wb[sheet_name]

        # Build header-name -> column-number map from template row 4
        template_col_map: Dict[str, int] = {}
        max_data_col = 0
        for cell in ws[HEADER_ROW]:
            if cell.value is not None:
                template_col_map[str(cell.value).strip()] = cell.column
                max_data_col = max(max_data_col, cell.column)

        # Cache header-row cell objects
        hdr_cells: Dict[int, Any] = {
            cell.column: cell for cell in ws[HEADER_ROW]
        }

        # Clear existing data rows (row 5 to max_row)
        if ws.max_row >= DATA_START:
            ws.delete_rows(DATA_START, ws.max_row - DATA_START + 1)

        # Concatenate all periods' DataFrames for this sheet
        combined = pd.concat(sheet_data[sheet_name], ignore_index=True)

        # Source_Period column: one after the last original col
        sp_col     = max_data_col + 1
        sp_ref_hdr = hdr_cells.get(max_data_col)

        # Add "Source_Period" header in row 4
        sp_hdr_cell = ws.cell(
            row=HEADER_ROW, column=sp_col, value='Source_Period'
        )
        copy_cell_style(sp_ref_hdr, sp_hdr_cell)

        # Write data rows (white background, black text)
        for r_offset, (_, row) in enumerate(combined.iterrows()):
            excel_row = DATA_START + r_offset

            # Write each original column matched by header name
            for col_name, col_num in template_col_map.items():
                raw = row.get(col_name)
                val = safe_value(raw)
                cell = ws.cell(row=excel_row, column=col_num, value=val)
                apply_data_style(hdr_cells.get(col_num), cell)

            # Write Source_Period value
            sp_cell = ws.cell(
                row=excel_row, column=sp_col,
                value=row.get('Source_Period', '')
            )
            apply_data_style(sp_ref_hdr, sp_cell)

    output_buffer = io.BytesIO()
    wb.save(output_buffer)
    output_buffer.seek(0)

    return output_buffer, auto_name, missing
