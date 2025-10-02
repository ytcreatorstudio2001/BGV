from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
import os

app = FastAPI()

# Load mapping file
MAPPING_FILE = "mappings.xlsx"
mappings_df = pd.read_excel(MAPPING_FILE)

@app.get("/")
def upload_form():
    formats = mappings_df["Format"].unique()
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
    df = pd.read_excel(file.file)

    # Filter mappings for selected format
    mapping = mappings_df[mappings_df["Format"] == format]

    df_out = pd.DataFrame()
    for _, row in mapping.iterrows():
        src, dest = row["Source Column"], row["Target Column"]
        if src in df.columns:
            df_out[dest] = df[src]
        else:
            df_out[dest] = ""  # blank if missing column

    out_file = f"{format}_output.xlsx"
    df_out.to_excel(out_file, index=False)

    return FileResponse(out_file, filename=out_file)
