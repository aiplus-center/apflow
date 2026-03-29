"""
WebSocket Executor for bidirectional communication

This executor allows tasks to communicate with WebSocket servers
for real-time bidirectional messaging.
"""

import asyncio
import json
from typing import ClassVar, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from apflow.core.base import BaseTask
from apflow.core.extensions.decorators import executor_register
from apflow.logger import get_logger

logger = get_logger(__name__)

try:
    import websockets
    from websockets.client import WebSocketClientProtocol  # noqa: F401

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning(
        "websockets is not installed. WebSocket executor will not be available. "
        "Install it with: pip install apflow[a2a] (websockets included in a2a extra)"
    )


class WebSocketInputSchema(BaseModel):
    url: str = Field(description="WebSocket URL to connect to (ws:// or wss://)")
    message: Union[str, Dict[str, Any]] = Field(
        description="Message to send (string or object that will be JSON-encoded)"
    )
    wait_response: bool = Field(
        default=True,
        description="Whether to wait for a response after sending the message",
    )
    timeout: float = Field(default=30.0, description="Connection and response timeout in seconds")
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional HTTP headers to include in the WebSocket handshake",
    )


class WebSocketOutputSchema(BaseModel):
    success: bool = Field(description="Whether the WebSocket communication was successful")
    error: Optional[str] = Field(
        default=None, description="Error message (only present on failure)"
    )
    url: Optional[str] = Field(default=None, description="WebSocket URL that was connected to")
    message_sent: Optional[str] = Field(
        default=None,
        description="Message that was sent (JSON string if object was sent)",
    )
    response: Optional[Any] = Field(
        default=None,
        description="Response received (string or parsed JSON object)",
    )
    wait_response: Optional[bool] = Field(
        default=None, description="Whether a response was expected"
    )
    code: Optional[int] = Field(
        default=None,
        description="WebSocket close code (only present for connection closed errors)",
    )
    reason: Optional[str] = Field(
        default=None,
        description="WebSocket close reason (only present for connection closed errors)",
    )


@executor_register()
class WebSocketExecutor(BaseTask):
    """
    Executor for WebSocket bidirectional communication

    Supports sending messages and receiving responses.

    Example usage in task schemas:
    {
        "schemas": {
            "method": "websocket_executor"  # Executor id
        },
        "inputs": {
            "url": "ws://example.com/ws",
            "message": "Hello",
            "wait_response": true,
            "timeout": 30
        }
    }
    """

    id = "websocket_executor"
    name = "WebSocket Executor"
    description = "Bidirectional WebSocket communication"
    tags = ["websocket", "ws", "realtime", "bidirectional"]
    examples = [
        "Send message via WebSocket",
        "Real-time communication",
        "WebSocket-based service integration",
    ]

    # Cancellation support: Can be cancelled by closing WebSocket connection
    cancelable: bool = True

    inputs_schema: ClassVar[type[BaseModel]] = WebSocketInputSchema
    outputs_schema: ClassVar[type[BaseModel]] = WebSocketOutputSchema

    @property
    def type(self) -> str:
        """Extension type identifier for categorization"""
        return "websocket"

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a WebSocket communication

        Args:
            inputs: Dictionary containing:
                - url: WebSocket URL (required)
                - message: Message to send (required)
                - wait_response: Whether to wait for response (default: True)
                - timeout: Connection timeout in seconds (default: 30.0)
                - headers: Optional HTTP headers dict for connection

        Returns:
            Dictionary with communication results:
                - message_sent: Sent message
                - response: Received response (if wait_response=True)
                - success: Boolean indicating success
        """
        url = inputs.get("url")
        if not url:
            raise ValueError("url is required in inputs")

        message = inputs.get("message")
        if not message:
            raise ValueError("message is required in inputs")

        if not WEBSOCKETS_AVAILABLE:
            return {
                "success": False,
                "error": "websockets is not installed. Install it with: pip install apflow[a2a]",
            }

        wait_response = inputs.get("wait_response", True)
        timeout = inputs.get("timeout", 30.0)
        headers = inputs.get("headers", {})

        logger.info(f"Connecting to WebSocket {url} and sending message")

        try:
            # Check for cancellation before connecting
            if self.cancellation_checker and self.cancellation_checker():
                logger.info("WebSocket communication cancelled before connection")
                return {"success": False, "error": "Communication was cancelled", "url": url}

            # Connect to WebSocket
            async with websockets.connect(
                url,
                extra_headers=headers if headers else None,
                ping_interval=None,  # Disable ping for short connections
            ) as websocket:
                # Check for cancellation after connection
                if self.cancellation_checker and self.cancellation_checker():
                    logger.info("WebSocket communication cancelled after connection")
                    return {"success": False, "error": "Communication was cancelled", "url": url}

                # Send message
                if isinstance(message, dict):
                    message_str = json.dumps(message)
                else:
                    message_str = str(message)

                await websocket.send(message_str)
                logger.debug(f"Sent message to {url}: {message_str}")

                # Wait for response if requested
                response = None
                if wait_response:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=timeout)

                        # Try to parse as JSON
                        try:
                            response = json.loads(response)
                        except (json.JSONDecodeError, TypeError):
                            pass  # Keep as string if not JSON

                        logger.debug(f"Received response from {url}: {response}")
                    except asyncio.TimeoutError:
                        logger.warning(f"WebSocket response timeout after {timeout} seconds")
                        return {
                            "success": False,
                            "error": f"Response timeout after {timeout} seconds",
                            "url": url,
                            "message_sent": message_str,
                        }

                # Check for cancellation after receiving response
                if self.cancellation_checker and self.cancellation_checker():
                    logger.info("WebSocket communication cancelled after response")
                    return {
                        "success": False,
                        "error": "Communication was cancelled",
                        "url": url,
                        "message_sent": message_str,
                        "response": response,
                    }

                return {
                    "success": True,
                    "url": url,
                    "message_sent": message_str,
                    "response": response,
                    "wait_response": wait_response,
                }

        except websockets.exceptions.InvalidURI:
            logger.error(f"Invalid WebSocket URL: {url}")
            return {"success": False, "error": f"Invalid WebSocket URL: {url}", "url": url}
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
            return {
                "success": False,
                "error": f"Connection closed: {str(e)}",
                "url": url,
                "code": e.code,
                "reason": e.reason,
            }
        except asyncio.TimeoutError:
            logger.error(f"WebSocket connection timeout after {timeout} seconds: {url}")
            return {
                "success": False,
                "error": f"Connection timeout after {timeout} seconds",
                "url": url,
            }
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket communication: {e}", exc_info=True)
            return {"success": False, "error": str(e), "url": url}

    def get_demo_result(self, task: Any, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Provide demo WebSocket communication result"""
        import json

        url = inputs.get("url", "ws://demo.example.com")
        message = inputs.get("message", "Hello, WebSocket!")
        wait_response = inputs.get("wait_response", True)

        result = {
            "url": url,
            "message_sent": message if isinstance(message, str) else json.dumps(message),
            "connected": True,
            "success": True,
        }

        if wait_response:
            result["response"] = {
                "type": "message",
                "data": "Demo WebSocket response",
                "timestamp": "2024-01-01T00:00:00Z",
            }

        result["_demo_sleep"] = 0.2  # Simulate WebSocket connection and message exchange
        return result
