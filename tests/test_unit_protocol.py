import sys
import json
from pathlib import Path

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from src.http_protocol.http_protocol import HTTPProtocol


# Mock classes for auth_instance and message_sender_instance
class MockAuth:
    async def create_user_and_token(self):
        return "mock_token"

    async def get_user_id_from_token(self, token):
        return 123 if token == "mock_token" else None


class MockMessageSender:
    async def retrieve_messages(self):
        return ["message1", "message2"]

    async def retrieve_private_messages(self, user_id, recipient_id):
        return ["private_message1"] if user_id and recipient_id else []

    async def insert_message(self, user_id, text):
        return 1  # Mock message ID

    async def insert_private_message(self, message_id, recipient_id):
        pass  # Assume it just inserts a message


@pytest.mark.asyncio
async def test_handle_connect_success():
    auth_instance = MockAuth()
    message_sender_instance = MockMessageSender()
    protocol = HTTPProtocol(auth_instance, message_sender_instance)
    protocol.send_response = AsyncMock()

    await protocol.handle_connect()

    protocol.send_response.assert_called_once()
    response = protocol.send_response.call_args[0][0]
    assert b'"status": "success"' in response
    assert b'"user_id": 123' in response


@pytest.mark.asyncio
async def test_handle_connect_failure():
    auth_instance = MockAuth()
    auth_instance.create_user_and_token = AsyncMock(return_value=None)
    message_sender_instance = MockMessageSender()
    protocol = HTTPProtocol(auth_instance, message_sender_instance)
    protocol.send_error_response = AsyncMock()

    await protocol.handle_connect()

    # Check that send_error_response was called instead of send_response
    protocol.send_error_response.assert_called_once()
    error_response_call_args = protocol.send_error_response.call_args
    assert error_response_call_args is not None
    assert error_response_call_args[0][0].status_code == 500


async def delayed_response(*args, **kwargs):
    await asyncio.sleep(settings.max_request_time + 1)


@pytest.mark.asyncio
async def test_handle_request_timeout():
    protocol = HTTPProtocol(MockAuth(), MockMessageSender())
    protocol.handle_get_request = AsyncMock(side_effect=delayed_response)
    protocol.handle_post_request = AsyncMock(side_effect=delayed_response)
    protocol.send_error_response = AsyncMock()

    # Simulate a GET request
    request_headers = Mock()
    request_headers.method = b"GET"
    request_headers.target = b"/health"

    await protocol.handle_request(request_headers, b"")
    protocol.send_error_response.assert_called_once_with(settings.error_messages.request_timeout_error)


@pytest.mark.asyncio
async def test_handle_health():
    protocol = HTTPProtocol(MockAuth(), MockMessageSender())
    protocol.send_response = AsyncMock()

    await protocol.handle_health()

    protocol.send_response.assert_called_once()
    response = protocol.send_response.call_args[0][0]
    assert b'"status": "OK"' in response
