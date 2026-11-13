import pandas as pd
import numpy as np
import re
import os
import chardet
from openpyxl.styles import Alignment

# ================= 核心清洗引擎 =================
def preprocess_date_text(val):
    if pd.isna(val): return ""
    val = str(val).replace('\u200b', '').replace('\xa0', '').strip()
    val = re.sub(r'\(.*?\)|（.*?）|补录|上午|下午', '', val)
    return val.replace('年', '-').replace('月', '-').replace('日', '')

def check_dates_logic(df, do_unify_date, date_format_str):
    out_fmt = '%Y-%m-%d'
    if date_format_str: out_fmt = date_format_str.replace('2026', '%Y').replace('05', '%m').replace('13', '%d')
    error_rows = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or any(
                kw in str(col) for kw in ['日期', '时间', 'Date', 'date']):
            cleaned_col = []
            for idx, val in enumerate(df[col]):
                if pd.isna(val) or str(val).strip() == "": cleaned_col.append(''); continue
                if not do_unify_date: cleaned_col.append(
                    str(val) if isinstance(val, pd.Timestamp) else str(val)); continue
                val_str = preprocess_date_text(val).split(' ')[0]
                dt = None
                if re.match(r'^\d{8}$', val_str):
                    try:
                        dt = pd.to_datetime(val_str, format='%Y%m%d')
                    except:
                        pass
                elif re.match(r'^\d{4,5}(\.\d+)?$', val_str):
                    try:
                        dt = pd.to_datetime(float(val_str), unit='D', origin='1899-12-30')
                    except:
                        pass
                if not dt:
                    try:
                        dt = pd.to_datetime(val_str)
                    except:
                        pass
                if dt and dt.year != 1900:
                    cleaned_col.append(dt.strftime(out_fmt))
                else:
                    cleaned_col.append(str(val))
                    if (idx + 2) not in error_rows: error_rows.append(idx + 2)
            df[col] = [str(x) if x is not None else '' for x in cleaned_col]
    return df, error_rows

def check_amount_logic_only(df):
    qty_col = next((c for c in df.columns if '数量' in str(c)), None)
    price_col = next((c for c in df.columns if '单价' in str(c)), None)
    amt_col = next((c for c in df.columns if '金额' in str(c) and '含税' not in str(c)), None)
    if not (qty_col and price_col and amt_col): return df, []
    error_rows = []
    for idx in range(len(df)):
        try:
            qty = pd.to_numeric(df.at[idx, qty_col], errors='coerce')
            price = pd.to_numeric(df.at[idx, price_col], errors='coerce')
            amt = pd.to_numeric(df.at[idx, amt_col], errors='coerce')
            if pd.isna(qty) or pd.isna(price) or pd.isna(amt): continue
            if not np.isclose(qty * price, amt, atol=0.01): error_rows.append(idx + 2)
        except:
            pass
    return df, error_rows

def clean_numbers(df, clean_noise, convert_units, remove_currency):
    num_cols = [col for col in df.columns if any(
        kw in str(col) for kw in ['金额', '单价', '数量', '费用', '额度', '销售额', '采购额', '工资', '税率'])]
    unit_map = {'百': 100, '千': 1000, '万': 10000, '十万': 100000, '百万': 1000000, '千万': 10000000, '亿': 100000000,
                'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
    for col in num_cols:
        cleaned_col = []
        for val in df[col]:
            if pd.isna(val) or str(val).strip() == "" or str(val) in ['-', 'N/A', '暂无', '暂估']: cleaned_col.append(
                ''); continue
            val_str = str(val).strip()
            if val_str.startswith('(') and val_str.endswith(')'): val_str = '-' + val_str[1:-1]
            if convert_units:
                for unit in sorted(unit_map.keys(), key=len, reverse=True):
                    if unit in val_str.lower():
                        num_part = re.sub(r'[^\d.-]', '', val_str.lower().replace(unit, ''))
                        try:
                            val_str = str(float(num_part) * unit_map[unit]);
                            break
                        except:
                            pass
            if remove_currency: val_str = re.sub(r'[￥$€£¥]', '', val_str)
            if clean_noise: val_str = re.sub(r'[^\d.-]', '', val_str)
            try:
                cleaned_col.append(float(val_str) if '.' in val_str else int(val_str))
            except:
                cleaned_col.append(val)
        df[col] = cleaned_col
    return df

def clean_phones(df):
    for col in df.columns:
        if any(kw in str(col) for kw in ['电话', '手机', '联系方式', 'Phone', 'phone']):
            cleaned_col = []
            for val in df[col]:
                if pd.isna(val) or str(val).strip() == "": cleaned_col.append(''); continue
                val_str = re.sub(r'[^\d]', '', str(val))
                if len(val_str) == 13 and val_str.startswith('86'): val_str = val_str[2:]
                cleaned_col.append(val_str)
            df[col] = cleaned_col
    return df

def clean_text_noise(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(r'[\r\n\t]', ' ', regex=True)
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()
            df[col] = df[col].replace('nan', '')
    return df

def clean_desensitize(df, desensitize_df):
    if desensitize_df is None or not isinstance(desensitize_df, pd.DataFrame) or len(desensitize_df) == 0: return df
    rules = {str(row["列名"]).strip(): str(row["脱敏规则"]).strip() for _, row in desensitize_df.iterrows() if
             str(row["列名"]).strip() in df.columns and str(row["脱敏规则"]).strip() not in ["不脱敏", ""]}
    for col, rule in rules.items():
        cleaned_col = []
        for val in df[col]:
            if pd.isna(val) or str(val).strip() == "": cleaned_col.append(''); continue
            val_str = str(val).strip()
            if rule == "手机号":
                clean_num = re.sub(r'[^\d]', '', val_str)
                if len(clean_num) >= 7: val_str = f"{clean_num[:3]}****{clean_num[-4:]}" if len(
                    clean_num) == 11 else val_str
            elif rule == "身份证":
                if len(val_str) >= 10: val_str = f"{val_str[:6]}********{val_str[-4:]}"
            elif rule == "姓名":
                if 1 < len(val_str) <= 5:
                    if len(val_str) == 2:
                        val_str = val_str[0] + '*'
                    elif len(val_str) >= 3:
                        val_str = val_str[0] + '*' * (len(val_str) - 2) + val_str[-1]
            elif rule == "邮箱":
                if '@' in val_str:
                    parts = val_str.split('@')
                    name_part = parts[0]
                    val_str = f"{name_part[:2]}***@{parts[1]}" if len(
                        name_part) > 2 else f"{name_part[0]}***@{parts[1]}"
            cleaned_col.append(val_str)
        df[col] = cleaned_col
    return df

def drop_summary_rows(df):
    mask = pd.Series(False, index=df.index)
    for col in df.columns[:2]: mask |= df[col].astype(str).str.contains('小计|合计|续上页|审核|注：|制表', na=False)
    return df[~mask]

def auto_calculate_fields(df, calc_amount, calc_price, calc_qty):
    qty_col = next((c for c in df.columns if '数量' in str(c)), None)
    price_col = next((c for c in df.columns if '单价' in str(c)), None)
    amt_col = next((c for c in df.columns if '金额' in str(c) and '含税' not in str(c)), None)
    if not (qty_col and price_col and amt_col): return df
    for idx in range(len(df)):
        try:
            qty = pd.to_numeric(df.at[idx, qty_col], errors='coerce')
            price = pd.to_numeric(df.at[idx, price_col], errors='coerce')
            amt = pd.to_numeric(df.at[idx, amt_col], errors='coerce')
            if calc_amount and pd.isna(amt) and not pd.isna(qty) and not pd.isna(price):
                df.at[idx, amt_col] = round(qty * price, 2)
            elif calc_qty and pd.isna(qty) and not pd.isna(amt) and not pd.isna(price) and price != 0:
                df.at[idx, qty_col] = round(amt / price, 2)
            elif calc_price and pd.isna(price) and not pd.isna(amt) and not pd.isna(qty) and qty != 0:
                df.at[idx, price_col] = round(amt / qty, 2)
        except:
            pass
    return df

def add_total_row(df):
    if df.empty: return df
    sum_cols = [col for col in df.columns if any(
        kw in str(col) for kw in ['数量', '金额', '费用', '额度', '销售额', '采购额', '工资']) and '单价' not in str(
        col)]
    if not sum_cols: return df
    total_row = {col: '' for col in df.columns}
    if len(df.columns) > 0: total_row[df.columns[0]] = '合计'
    for col in sum_cols:
        numeric_vals = pd.to_numeric(df[col], errors='coerce')
        total_sum = numeric_vals.sum()
        total_row[col] = int(total_sum) if total_sum == int(total_sum) else round(total_sum, 2)
    return pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

def find_smart_header(df_raw):
    best_row = 0;
    max_score = -1
    keywords = ['日期', '时间', '客户', '名称', '订单', '金额', '单价', '数量', '费用', '部门', '备注', '业务员',
                '产品']
    for i in range(min(15, len(df_raw))):
        row_vals = [str(x) for x in df_raw.iloc[i].dropna().tolist()]
        if not row_vals: continue
        score = len(row_vals) * 2 + sum(1 for val in row_vals for kw in keywords if kw in val) * 10
        if len(row_vals) <= 2 and any(len(str(x)) > 10 for x in row_vals): score -= 100
        if score > max_score: max_score = score; best_row = i
    return best_row

def apply_excel_alignment(writer, df_s, s_name, num_align_rule, text_align_rule, header_align_rule):
    sheet = writer.sheets[s_name]
    rule_map = {"左对齐": "left", "居中": "center", "右对齐": "right", "不更改": None}
    num_align, text_align, header_align = rule_map.get(num_align_rule), rule_map.get(text_align_rule), rule_map.get(
        header_align_rule)
    num_cols = [col for col in df_s.columns if any(
        kw in str(col) for kw in ['金额', '单价', '数量', '费用', '额度', '销售额', '采购额', '工资', '税率'])]
    for row_idx in range(1, len(df_s) + 2):
        for col_idx, col_name in enumerate(df_s.columns, start=1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            if row_idx == 1:
                if header_align: cell.alignment = Alignment(horizontal=header_align, vertical="center")
            else:
                if col_name in num_cols:
                    if num_align: cell.alignment = Alignment(horizontal=num_align, vertical="center")
                else:
                    if text_align: cell.alignment = Alignment(horizontal=text_align, vertical="center")

def align_columns(df):
    synonyms = {
        '客户名称': ['客户', '名字', '客户全称', '购买方', '供应商名称', 'Customer', '客 户 名 称'],
        '日期': ['时间', '成交日期', '下单日期', '发生日期', 'Date', '日 期'],
        '数量': ['购买数量', '件数', '销量', '数量(台)', 'Qty', '数 量'],
        '单价': ['价格', '单价(元)', 'Unit Price', '单 价'],
        '金额': ['总金额', '金额(元)', '费用', '销售额', '采购额', 'Amount', '金　　额'],
        '订单号': ['订单编号', 'Order No', '订单号'],
        '业务员': ['销售员', '销售代表', '业务人员', '负责人', '销售'],
        '备注': ['备注(隐藏列)', '备注']
    }
    new_cols = {}
    for col in df.columns:
        clean_c = str(col).replace('\n', '').replace(' ', '').replace('　', '').strip()
        matched = False
        for std_name, syns in synonyms.items():
            if clean_c == std_name or clean_c in syns: new_cols[col] = std_name; matched = True; break
        if not matched: new_cols[col] = str(col).strip()
    return df.rename(columns=new_cols)

def smart_read_file(file_path, is_multi_file=False, header_row=None):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.xlsx', '.xls']:
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            xls = pd.ExcelFile(file_path, engine=engine)
            dfs = []
            for sheet in xls.sheet_names:
                if sheet in ['说明']: continue
                df_raw = pd.read_excel(file_path, sheet_name=sheet, header=None, engine=engine)
                if df_raw.empty: continue
                h_idx = header_row if header_row is not None else find_smart_header(df_raw)
                df = pd.read_excel(file_path, sheet_name=sheet, header=h_idx, engine=engine)
                if any(str(c).startswith('Unnamed') for c in df.columns) and h_idx > 0:
                    top_row = df_raw.iloc[h_idx - 1].fillna('')
                    new_cols = [f"{top}_{c}" if str(c).startswith('Unnamed') and str(top).strip() else c for c, top in
                                zip(df.columns, top_row)]
                    df.columns = new_cols
                for col in df.columns:
                    if '万元' in str(col):
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace('万', ''), errors='coerce') * 10000
                        df = df.rename(columns={col: str(col).replace('(万元)', '').replace('（万元）', '')})
                dfs.append((sheet, df))
            return dfs
        elif ext == '.csv':
            with open(file_path, 'rb') as f:
                enc = chardet.detect(f.read(10000))['encoding']
            df_raw = pd.read_csv(file_path, encoding=enc, header=None)
            return [("CSV数据", pd.read_csv(file_path, encoding=enc, header=find_smart_header(df_raw)))]
        elif ext == '.txt':
            df_raw = pd.read_csv(file_path, sep='\t', encoding='utf-8-sig', header=None)
            return [("TXT数据",
                     pd.read_csv(file_path, sep='\t', encoding='utf-8-sig', header=find_smart_header(df_raw)).dropna(
                         how='all'))]
    except Exception:
        return []
    return []

def apply_cleaning_pipeline(df, drop_empty, drop_dup, drop_summary, do_fill, fill_text, do_clean_num, clean_noise,
                            convert_units, remove_currency, do_clean_phone, do_unify_date, date_format_str,
                            do_auto_calc, calc_amount, calc_price, calc_qty, do_check_logic, do_replace, replace_column,
                            rename_map_df, sheet_name=""):
    df_clean = df.copy()

    if drop_empty: df_clean = df_clean.dropna(how='all')
    if drop_summary: df_clean = drop_summary_rows(df_clean)
    df_clean = clean_text_noise(df_clean)
    if do_fill and fill_text: df_clean = df_clean.fillna(fill_text)
    df_clean = df_clean.reset_index(drop=True)

    if do_clean_phone: df_clean = clean_phones(df_clean)
    if do_clean_num: df_clean = clean_numbers(df_clean, clean_noise, convert_units, remove_currency)

    if replace_column and rename_map_df is not None and isinstance(rename_map_df, pd.DataFrame) and len(
            rename_map_df) > 0:
        if replace_column in df_clean.columns:
            try:
                df_clean[replace_column] = df_clean[replace_column].astype(str).str.strip()
                valid_maps = rename_map_df[
                    rename_map_df["原值"].astype(str).str.strip() != rename_map_df["统一为"].astype(str).str.strip()]
                mapping_dict = {str(row["原值"]).strip(): str(row["统一为"]).strip() for _, row in
                                valid_maps.iterrows()}
                if mapping_dict:
                    df_clean[replace_column] = df_clean[replace_column].replace(mapping_dict)
            except Exception as e:
                pass

    df_clean, date_errs = check_dates_logic(df_clean, do_unify_date, date_format_str)
    if do_auto_calc: df_clean = auto_calculate_fields(df_clean, calc_amount, calc_price, calc_qty)

    logic_errs = []
    if do_check_logic:
        df_clean, logic_errs = check_amount_logic_only(df_clean)

    if drop_dup: df_clean = df_clean.drop_duplicates()

    sheet_errors = []
    if date_errs or logic_errs:
        error_str = f"**【{sheet_name}】**\n" if sheet_name else ""
        if date_errs:
            error_str += f"- **日期无法识别**：第 {'、'.join([str(x) for x in sorted(date_errs)])} 行\n"
        if logic_errs:
            error_str += f"- **金额计算异常**（数量×单价≠金额）：第 {'、'.join([str(x) for x in sorted(logic_errs)])} 行\n"
        sheet_errors.append(error_str.strip())

    return df_clean, sheet_errors