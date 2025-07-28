from fastapi.responses import HTMLResponse
from fastapi import File, UploadFile, Form
import shutil
import os

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/ask_ui", response_class=HTMLResponse)
def ask_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ask API with File Upload</title>
    </head>
    <body>
        <h2>Ask the Model</h2>
        <form id="askForm">
            <input type="text" id="query" name="query" size="80" placeholder="Type your query"><br><br>
            <input type="file" id="file" name="file"><br><br>
            <button type="button" onclick="sendQuery()">Submit</button>
        </form>
        <pre id="result"></pre>

        <script>
        async function sendQuery() {
            const formData = new FormData();
            const query = document.getElementById("query").value;
            const file = document.getElementById("file").files[0];
            formData.append("query", query);
            if (file) formData.append("file", file);

            let res = await fetch("/ask_with_file", {
                method: "POST",
                body: formData
            });
            let data = await res.json();
            document.getElementById("result").textContent = JSON.stringify(data, null, 2);
        }
        </script>
    </body>
    </html>
    """

@app.post("/ask_with_file")
async def ask_with_file(query: str = Form(...), file: UploadFile = File(None)):
    file_path = None
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # For now, just return info about the upload and query
    # You can integrate file content into embeddings later
    return {
        "query": query,
        "file_uploaded": bool(file),
        "file_saved_at": file_path
    }
