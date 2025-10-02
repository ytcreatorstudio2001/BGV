from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
import os

app = FastAPI()

# Folder containing mapping files
MAPPING_FOLDER = "mappings"
mapping_files = os.listdir(MAPPING_FOLDER)
formats = [f.split(".")[0] for f in mapping_files]  # ['BGV', 'NJ', 'Swayam']

@app.get("/")
def upload_form():
    options = "".join([f'<option value="{f}">{f}</option>' for f in formats])
    return HTMLResponse(f"""
    <html>
        <body>
            <h2>Candidate Excel Converter</h2>
            <form action="/convert" enctype="multipart/form-data" method="post">
                <input type="file" name="file" required><br><br>
                <label>Select Output Format:</label>
                <select name="format">{options}</select><br><br>
                <input type="submit" value="Generate">
            </form>
        </body>
    </html>
    """)

@app.post("/convert")
async def convert(file: UploadFile, format: str = Form(...)):
    # Load selected mapping file
    mapping_path = os.path.join(MAPPING_FOLDER, f"{format}.xlsx")
    mapping_df = pd.read_excel(mapping_path)

    # Load uploaded bulk data
    df = pd.read_excel(file.file)

    # Create output dataframe
    df_out = pd.DataFrame()
    for _, row in mapping_df.iterrows():
        output_col = row["Output Header"]
        source_col = row["Source Header"]
        if source_col in df.columns:
            df_out[output_col] = df[source_col]
        else:
            df_out[output_col] = ""  # blank if source column missing

    out_file = f"{format}_output.xlsx"
    df_out.to_excel(out_file, index=False)

    return FileResponse(out_file, filename=out_file)
