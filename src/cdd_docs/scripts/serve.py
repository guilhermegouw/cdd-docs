"""Script to serve the FastAPI chat API."""

import uvicorn


def main():
    """Run the FastAPI server."""
    print("Starting CDD Docs Chat API...")
    print("API: http://localhost:8000/chat")
    print("Docs: http://localhost:8000/docs")
    print()

    uvicorn.run(
        "cdd_docs.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
