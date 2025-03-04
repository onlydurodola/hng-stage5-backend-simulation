import asyncio
import json
import os
import git
import websockets
from datetime import datetime

# GitLab repo details
REPO_URL = "https://gitlab.com/yourusername/backend-im-code.git"  # Replace with your repo
REPO_DIR = "local_backend_im_repo"
USERNAME = "yourusername"  # Your GitLab username
TOKEN = "your_personal_access_token"  # From GitLab -> Settings -> Access Tokens
WS_URL = "ws://localhost:8000/ws/logs"  # orchestration-app WebSocket

async def push_code_to_git(code):
    """Push code to GitLab repo."""
    if not os.path.exists(REPO_DIR):
        repo = git.Repo.clone_from(f"https://{USERNAME}:{TOKEN}@{REPO_URL.split('https://')[1]}", REPO_DIR)
    else:
        repo = git.Repo(REPO_DIR)
    code_file = os.path.join(REPO_DIR, "code.py")
    with open(code_file, "w") as f:
        f.write(code)
    repo.index.add(["code.py"])
    repo.index.commit(f"Update code.py at {datetime.now()}")
    origin = repo.remote(name="origin")
    origin.push()

async def receive_logs():
    """Connect to WebSocket and receive logs."""
    async with websockets.connect(WS_URL) as websocket:
        print("Connected to WebSocket /ws/logs")
        await websocket.send(json.dumps({"subscribe": True}))
        while True:
            log = await websocket.recv()
            log_data = json.loads(log)
            print(f"Received log: {log_data}")
            if log_data["level"] == "ERROR" and "Test result: tests_failed" in log_data["message"]:
                print("Debugging: Fixing code based on logs...")
                fixed_code = "print('Fixed code from test')"  # Example fix
                await push_code_to_git(fixed_code)
            elif "Test result: deployed" in log_data["message"]:
                print("Success: Deployment complete! Access at https://test.backend.im")
                break

async def main():
    # Initial bad code to trigger failure
    bad_code = "print('Buggy code"  # Missing parenthesis
    await push_code_to_git(bad_code)
    await receive_logs()

if __name__ == "__main__":
    asyncio.run(main())