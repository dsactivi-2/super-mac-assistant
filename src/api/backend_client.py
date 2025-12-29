"""
Backend API Client
Connects to Code Cloud Agents Backend (localhost:3000)
Supports both REST API and WebSocket
"""

import requests
import json
from typing import Dict, Optional, List
from websocket import create_connection, WebSocket
import threading
import time


class BackendAPIClient:
    """Client for Code Cloud Agents Backend API"""

    def __init__(self, base_url: str = "http://localhost:3000", ws_url: str = "ws://localhost:3000/ws"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.ws: Optional[WebSocket] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.connected = False
        self.token: Optional[str] = None
        self.message_handlers = []

    def connect(self) -> bool:
        """Check if backend is reachable"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.connected = response.status_code == 200
            print(f"✅ Backend connected: {self.base_url}")
            return self.connected
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            self.connected = False
            return False

    def login(self, email: str, password: str) -> bool:
        """Login to backend and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("accessToken")
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get auth headers"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ============================================================================
    # TASK MANAGEMENT
    # ============================================================================

    def create_task(self, title: str, description: str = "", priority: str = "medium", assignee: str = "cloud_assistant") -> Dict:
        """Create a new task"""
        try:
            response = requests.post(
                f"{self.base_url}/api/tasks",
                json={
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "assignee": assignee
                },
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200 or response.status_code == 201:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_tasks(self, status: Optional[str] = None) -> Dict:
        """List all tasks"""
        try:
            params = {}
            if status:
                params["status"] = status
            response = requests.get(
                f"{self.base_url}/api/tasks",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_task(self, task_id: str) -> Dict:
        """Get task details"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tasks/{task_id}",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # CHAT & MEMORY
    # ============================================================================

    def send_chat_message(self, message: str, agent_name: str = "emir", user_id: str = "local_user") -> Dict:
        """Send a chat message to an agent"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/send",
                json={
                    "message": message,
                    "userId": user_id,
                    "agentName": agent_name,
                    "provider": "anthropic",
                    "model": "claude-3.5-sonnet"
                },
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_chat_history(self, user_id: str = "local_user") -> Dict:
        """Get chat history"""
        try:
            response = requests.get(
                f"{self.base_url}/api/memory/chats/{user_id}",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # SLACK INTEGRATION
    # ============================================================================

    def send_slack_message_as_agent(self, agent_type: str, user_id: str, message: str) -> Dict:
        """
        Send Slack message as specific agent
        agent_type: 'supervisor' or 'assistant'
        """
        try:
            # This will be handled by the backend's Slack integration
            # We'll create a custom endpoint for agent-specific messages
            response = requests.post(
                f"{self.base_url}/api/agents/slack/send",
                json={
                    "agentType": agent_type,
                    "userId": user_id,
                    "message": message
                },
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # GITHUB INTEGRATION
    # ============================================================================

    def github_create_issue(self, repo: str, title: str, body: str = "", labels: List[str] = None) -> Dict:
        """Create GitHub issue"""
        try:
            response = requests.post(
                f"{self.base_url}/api/github/issues",
                json={
                    "repo": repo,
                    "title": title,
                    "body": body,
                    "labels": labels or []
                },
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # LINEAR INTEGRATION
    # ============================================================================

    def linear_create_issue(self, title: str, description: str = "", team_id: Optional[str] = None) -> Dict:
        """Create Linear issue"""
        try:
            payload = {
                "title": title,
                "description": description
            }
            if team_id:
                payload["teamId"] = team_id

            response = requests.post(
                f"{self.base_url}/api/linear/issues",
                json=payload,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # WEBSOCKET
    # ============================================================================

    def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        if self.ws and self.ws.connected:
            print("⚠️  WebSocket already connected")
            return

        try:
            ws_url_with_token = f"{self.ws_url}?token={self.token}" if self.token else self.ws_url
            self.ws = create_connection(ws_url_with_token)
            self.ws_thread = threading.Thread(target=self._ws_listen, daemon=True)
            self.ws_thread.start()
            print("✅ WebSocket connected")
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")

    def _ws_listen(self):
        """Listen for WebSocket messages"""
        while self.ws and self.ws.connected:
            try:
                message = self.ws.recv()
                if message:
                    data = json.loads(message)
                    self._handle_ws_message(data)
            except Exception as e:
                print(f"WebSocket error: {e}")
                break

    def _handle_ws_message(self, data: Dict):
        """Handle incoming WebSocket message"""
        print(f"📨 WebSocket message: {data.get('type', 'unknown')}")

        # Notify all registered handlers
        for handler in self.message_handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Handler error: {e}")

    def add_message_handler(self, handler):
        """Add a handler for WebSocket messages"""
        self.message_handlers.append(handler)

    def disconnect_websocket(self):
        """Disconnect WebSocket"""
        if self.ws:
            self.ws.close()
            self.ws = None
            print("WebSocket disconnected")


# Example usage
if __name__ == "__main__":
    client = BackendAPIClient()

    # Test connection
    if client.connect():
        print("✅ Backend is running!")

        # Test task creation
        result = client.create_task(
            title="Test task from Mac Assistant",
            description="Testing the API integration",
            priority="low"
        )
        print(f"Task creation: {result}")
    else:
        print("❌ Backend is not running. Start it with: cd ~/activi-dev-repos/Optimizecodecloudagents && npm run backend:dev")
