import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run("hydroships.app:create_app", factory=True,
                host=os.environ.get("HYDROSHIPS_HOST", "127.0.0.1"),
                port=int(os.environ.get("HYDROSHIPS_PORT", "8081")), workers=1)
