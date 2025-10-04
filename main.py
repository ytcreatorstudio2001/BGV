from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
import os

app = FastAPI()

# Folder containing mapping files
MAPPING_FOLDER = "Mappings"
os.makedirs(MAPPING_FOLDER, exist_ok=True)  # Ensure folder exists

# Read available mapping formats
mapping_files = os.listdir(MAPPING_FOLDER)
formats = [f.split(".")[0] for f in mapping_files] if mapping_files else []


@app.get("/")
def upload_form():
    options = "".join([f'<option value="{f}">{f}</option>' for f in formats])
    return HTMLResponse(f"""
    <html>
        <head>
            <title>Candidate Excel Converter</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h2 {{ color: #333; }}
                form {{ background: #f9f9f9; padding: 20px; border-radius: 10px; width: 400px; }}
                input, select {{ margin: 10px 0; padding: 8px; width: 100%; }}
                input[type=submit] {{
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    cursor: pointer;
                    border-radius: 5px;
                }}
                input[type=submit]:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <h2>Candidate Excel Converter</h2>
            <form action="/convert" enctype="multipart/form-data" method="post">
                <input type="file" name="file" required><br>
                <label>Select Output Format:</label>
                <select name="format" required>{options}</select><br>
                <input type="submit" value="Generate">
            </form>
        </body>
    </html>
    """)


@app.post("/convert")
async def convert(file: UploadFile, format: str = Form(...)):
    mapping_path = os.path.join(MAPPING_FOLDER, f"{format}.xlsx")

    # Validate mapping file existence
    if not os.path.exists(mapping_path):
        return HTMLResponse(f"<h3>Mapping file for '{format}' not found in {MAPPING_FOLDER}/</h3>", status_code=400)

    # Load mapping and uploaded file
    mapping_df = pd.read_excel(mapping_path)
    df = pd.read_excel(file.file, dtype=str)  # Force everything as text

    # Create output DataFrame based on mapping
    df_out = pd.DataFrame()
    for _, row in mapping_df.iterrows():
        output_col = row.get("Output Header")
        source_col = row.get("Source Header")
        if source_col in df.columns:
            df_out[output_col] = df[source_col]
        else:
            df_out[output_col] = ""  # blank if column missing

    # Convert only valid date-like columns to DD-MMM-YYYY
    for col in df_out.columns:
        temp = pd.to_datetime(df_out[col], errors="coerce")
        if temp.notna().any():  # if at least one valid date
            df_out[col] = temp.dt.strftime("%d-%b-%Y")
        else:
            df_out[col] = df_out[col].astype(str)  # keep as text

    # Save final output
    out_file = f"{format}_output.xlsx"
    df_out.to_excel(out_file, index=False)

    return FileResponse(out_file, filename=out_file)
