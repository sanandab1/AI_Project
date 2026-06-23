import requests
import time
from typing import Any, Dict
from loan_ai_system.services.logger_service import StructuredLogger

logger = StructuredLogger(__name__)

class MCPClient:
    MAX_RETRIES = 3
    BASE_WAIT_TIME = 2
    MAX_WAIT_TIME = 10
    TIMEOUT = 30

    @classmethod
    def call_mcp(cls, tool: str, payload: Dict[str, Any], correlation_id: str = None) -> Any:
        if correlation_id:
            logger.set_correlation_id(correlation_id)

        for attempt in range(cls.MAX_RETRIES):
            try:
                logger.debug(
                    f"MCP call attempt {attempt + 1}/{cls.MAX_RETRIES}",
                    tool=tool,
                    payload_keys=list(payload.keys()) if isinstance(payload, dict) else None
                )

                res = requests.post(
                    "http://localhost:9000/mcp",
                    json={"tool_name": tool, "input": payload},
                    timeout=cls.TIMEOUT
                )
                res.raise_for_status()
                data = res.json()

                if "output" not in data:
                    raise ValueError(f"MCP response missing 'output' field: {data}")

                logger.info(f"MCP call successful for tool '{tool}'", tool=tool)
                return data["output"]

            except requests.exceptions.Timeout as e:
                logger.warning(
                    f"MCP call timeout on attempt {attempt + 1}",
                    tool=tool,
                    error=str(e)
                )
                if attempt < cls.MAX_RETRIES - 1:
                    wait_time = min(cls.BASE_WAIT_TIME * (2 ** attempt), cls.MAX_WAIT_TIME)
                    logger.debug(f"Waiting {wait_time}s before retry", wait_seconds=wait_time)
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"MCP timeout for tool '{tool}' after {cls.MAX_RETRIES} attempts: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"MCP connection error on attempt {attempt + 1}",
                    tool=tool,
                    error=str(e)
                )
                if attempt < cls.MAX_RETRIES - 1:
                    wait_time = min(cls.BASE_WAIT_TIME * (2 ** attempt), cls.MAX_WAIT_TIME)
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Cannot connect to MCP server at localhost:9000. Make sure it's running. Last error: {str(e)}")

            except ValueError as e:
                logger.error(f"MCP response validation failed", tool=tool, error=str(e))
                raise RuntimeError(f"Invalid MCP response for tool '{tool}': {str(e)}")

            except Exception as e:
                logger.error(f"MCP call failed", tool=tool, error=str(e), attempt=attempt + 1)
                if attempt < cls.MAX_RETRIES - 1:
                    wait_time = min(cls.BASE_WAIT_TIME * (2 ** attempt), cls.MAX_WAIT_TIME)
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"MCP call failed for tool '{tool}' after {cls.MAX_RETRIES} attempts: {str(e)}")

def call_mcp(tool: str, payload: Dict[str, Any], correlation_id: str = None) -> Any:
    return MCPClient.call_mcp(tool, payload, correlation_id)