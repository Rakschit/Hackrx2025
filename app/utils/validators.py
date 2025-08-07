import os
import secrets
import requests
from mimetypes import guess_type
from urllib.parse import urlparse

from fastapi import Header, HTTPException, status

# --- Environment Variable Loading ---
BEARER_API_KEY = os.getenv("BEARER_API_KEY")

# --- Allowed File Types ---
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    # Add other supported types here
}

def verify_bearer(authorization: str = Header(None)):
    """
    FastAPI dependency to verify a Bearer token.
    Uses secrets.compare_digest to prevent timing attacks.
    """
    if not BEARER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: BEARER_API_KEY is not set."
        )
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Must use Bearer token."
        )

    # Extract the token from the "Bearer <token>" string
    sent_token = authorization.split(" ")[1]

    # Securely compare the sent token with the server's key
    if not secrets.compare_digest(sent_token, BEARER_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

def validate_document_url(doc_url: str) -> tuple[str, str]:
    """
    Validates the document URL and its content type without downloading the file.

    Args:
        doc_url: The URL of the document to validate.

    Returns:
        A tuple containing the (validated_url, file_extension).
    
    Raises:
        HTTPException: If the URL is invalid or the file type is not supported.
    """
    try:
        # Check the Content-Type header first using a HEAD request
        resp = requests.head(doc_url, stream=True, allow_redirects=True, timeout=10)
        resp.raise_for_status()  # Raise an exception for 4xx/5xx status codes
        doc_type = resp.headers.get("Content-Type", "").lower().split(";")[0].strip()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to access document URL: {e}"
        )
    finally:
        if 'resp' in locals():
            resp.close()

    # If Content-Type is missing, try to guess from the URL path extension
    if not doc_type:
        parsed_path = urlparse(doc_url).path
        mime, _ = guess_type(parsed_path)
        doc_type = mime or ""

    # Check if the determined MIME type is in our allowed list
    if doc_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{doc_type}'. Only PDF files are allowed."
        )
    
    file_extension = ALLOWED_MIME_TYPES[doc_type]
    return doc_url, file_extension


def download_file(doc_url: str, temp_path: str):
    """
    Downloads a file from a URL to a temporary path.
    """
    try:
        with requests.get(doc_url, timeout=15, stream=True) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        # Catch specific request-related errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Download failed: {e}"
        )