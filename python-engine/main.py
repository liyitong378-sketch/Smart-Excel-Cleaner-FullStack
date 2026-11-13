from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json
import os
import pandas as pd
from cleaner import apply_cleaning_pipeline, add_total_row, smart_read_file, clean_desensitize

app = FastAPI()

class ExecuteRequest(BaseModel):
    file_path: str
    config_json: str

class AnalyzeRequest(BaseModel):
    file_path: str

@app.get("/api/python/test")
def test_api():
    return {"status": "success", "message": "我是 Python 清洗引擎，我准备好了！"}

@app.post("/api/python/columns")
def get_columns(req: AnalyzeRequest):
    try:
        file_dfs = smart_read_file(req.file_path)
        if not file_dfs: return {"columns": []}
        return {"columns": list(file_dfs[0][1].columns)}
    except Exception as e:
        return {"columns": [], "error": str(e)}

@app.post("/api/python/preview")
def preview_cleaning(req: ExecuteRequest):
    try:
        config = json.loads(req.config_json)
        file_dfs = smart_read_file(req.file_path)
        if not file_dfs: return {"status": "error", "message": "文件读取失败", "sheets": []}
        
        results = []
        for sheet_name, df in file_dfs:
            try:
                df_clean, errors = apply_cleaning_pipeline(
                    df, 
                    drop_empty=config.get('dropEmpty', True), drop_dup=config.get('dropDup', True),
                    drop_summary=config.get('dropSummary', True), do_fill=config.get('doFill', False),
                    fill_text=config.get('fillText', '未知'), do_clean_num=config.get('doCleanNum', True),
                    clean_noise=config.get('cleanNoise', True), convert_units=config.get('convertUnits', True),
                    remove_currency=config.get('removeCurrency', True), do_clean_phone=config.get('doCleanPhone', True),
                    do_unify_date=config.get('doUnifyDate', False), date_format_str=config.get('dateFormat', '2026-05-13'),
                    do_auto_calc=config.get('doAutoCalc', True), calc_amount=config.get('calcAmount', True),
                    calc_price=config.get('calcPrice', True), calc_qty=config.get('calcQty', True),
                    do_check_logic=config.get('doCheckLogic', True), do_replace=False, replace_column=None,
                    rename_map_df=None, sheet_name=sheet_name
                )
                
                if config.get('doDesensitize', False):
                    desensitize_list = config.get('desensitizeList', [])
                    if desensitize_list:
                        desensitize_df = pd.DataFrame(desensitize_list).rename(columns={'columnName': '列名', 'rule': '脱敏规则'})
                        df_clean = clean_desensitize(df_clean, desensitize_df)
                        
                if config.get('doTotal', False): df_clean = add_total_row(df_clean)

                head_df = df_clean.head(100).copy()
                for col in head_df.columns:
                    head_df[col] = head_df[col].astype(str).replace('nan', '').replace('NaT', '').replace('None', '')

                results.append({
                    "name": sheet_name, "columns": list(head_df.columns),
                    "data": head_df.to_dict(orient='records'), "errors": errors
                })
            except Exception as sheet_err:
                import traceback
                traceback.print_exc()
                results.append({"name": sheet_name, "columns": [], "data": [], "errors": [f"**处理异常**：{str(sheet_err)}"]})

        return {"status": "success", "sheets": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e), "sheets": []}

@app.post("/api/python/execute")
def execute_cleaning(req: ExecuteRequest):
    try:
        config = json.loads(req.config_json)
        file_dfs = smart_read_file(req.file_path)
        if not file_dfs: return {"status": "error", "message": "文件读取失败"}
        
        file_dir, file_name = os.path.split(req.file_path)
        file_base, _ = os.path.splitext(file_name)
        output_path = os.path.join(file_dir, f"{file_base}_cleaned.xlsx")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in file_dfs:
                df_clean, errors = apply_cleaning_pipeline(
                    df, 
                    drop_empty=config.get('dropEmpty', True), drop_dup=config.get('dropDup', True),
                    drop_summary=config.get('dropSummary', True), do_fill=config.get('doFill', False),
                    fill_text=config.get('fillText', '未知'), do_clean_num=config.get('doCleanNum', True),
                    clean_noise=config.get('cleanNoise', True), convert_units=config.get('convertUnits', True),
                    remove_currency=config.get('removeCurrency', True), do_clean_phone=config.get('doCleanPhone', True),
                    do_unify_date=config.get('doUnifyDate', False), date_format_str=config.get('dateFormat', '2026-05-13'),
                    do_auto_calc=config.get('doAutoCalc', True), calc_amount=config.get('calcAmount', True),
                    calc_price=config.get('calcPrice', True), calc_qty=config.get('calcQty', True),
                    do_check_logic=config.get('doCheckLogic', True), do_replace=False, replace_column=None,
                    rename_map_df=None, sheet_name=sheet_name
                )
                
                if config.get('doDesensitize', False):
                    desensitize_list = config.get('desensitizeList', [])
                    if desensitize_list:
                        desensitize_df = pd.DataFrame(desensitize_list).rename(columns={'columnName': '列名', 'rule': '脱敏规则'})
                        df_clean = clean_desensitize(df_clean, desensitize_df)
                        
                if config.get('doTotal', False): df_clean = add_total_row(df_clean)
                    
                for col in df_clean.columns:
                    if '日期' in str(col) or '时间' in str(col):
                        df_clean[col] = df_clean[col].apply(lambda x: f"'{x}" if pd.notna(x) and str(x).strip() != '' else '')
                
                safe_sheet_name = str(sheet_name)[:30]
                df_clean.to_excel(writer, sheet_name=safe_sheet_name, index=False)

        return {"status": "success", "message": "清洗完成", "output_file": output_path}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"清洗报错了: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)