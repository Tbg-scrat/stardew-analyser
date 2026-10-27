import json
import urllib.error
from unittest.mock import MagicMock, mock_open, patch

from src.core.telemetry import TELEMETRY_URL, ping


@patch("src.core.telemetry.urllib.request.urlopen")
def test_telemetry_disabled_by_default(mock_urlopen, monkeypatch):
    """Verify telemetry does not execute when TELEMETRY_ENABLED is not set."""
    monkeypatch.delenv("TELEMETRY_ENABLED", raising=False)
    ping()
    mock_urlopen.assert_not_called()


@patch("src.core.telemetry.urllib.request.urlopen")
def test_telemetry_disabled_explicitly(mock_urlopen, monkeypatch):
    """Verify telemetry does not execute when TELEMETRY_ENABLED is set to false."""
    monkeypatch.setenv("TELEMETRY_ENABLED", "false")
    ping()
    mock_urlopen.assert_not_called()


@patch("src.core.telemetry.urllib.request.urlopen")
def test_telemetry_enabled_creates_new_id(mock_urlopen, monkeypatch):
    """Verify telemetry generates a new random UUID when enabled and no cache file exists."""
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("APP_VERSION", "2.0.0")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    m_file = mock_open(read_data="")
    with patch("os.path.exists", return_value=False), \
         patch("builtins.open", m_file), \
         patch("os.makedirs") as mock_makedirs:

        ping()

        mock_makedirs.assert_called_once_with("/cache/telemetry", exist_ok=True)
        
        # Verify urlopen was called with the correct edge URL and POST method
        mock_urlopen.assert_called_once()
        req_arg = mock_urlopen.call_args[0][0]
        assert req_arg.get_full_url() == TELEMETRY_URL
        assert req_arg.get_method() == "POST"
        
        # Validate payload structure and values
        sent_data = json.loads(req_arg.data.decode("utf-8"))
        assert "id" in sent_data
        assert len(sent_data["id"]) > 0
        assert sent_data["version"] == "2.0.0"


@patch("src.core.telemetry.urllib.request.urlopen")
def test_telemetry_enabled_uses_existing_id(mock_urlopen, monkeypatch):
    """Verify telemetry reads and reuses an existing instance ID if present."""
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("APP_VERSION", "2.1.0")

    existing_id = "test-uuid-1234-5678"
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    m_file = mock_open(read_data=existing_id)
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", m_file), \
         patch("os.makedirs"):

        ping()

        mock_urlopen.assert_called_once()
        req_arg = mock_urlopen.call_args[0][0]
        sent_data = json.loads(req_arg.data.decode("utf-8"))
        assert sent_data["id"] == existing_id
        assert sent_data["version"] == "2.1.0"


@patch("src.core.telemetry.urllib.request.urlopen")
def test_telemetry_handles_network_error(mock_urlopen, monkeypatch):
    """Verify that network errors (URLError) are caught gracefully without crashing."""
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    
    mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

    m_file = mock_open(read_data="some-existing-id")
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", m_file), \
         patch("os.makedirs"):

        # Should execute silently and catch the exception internally
        ping()
        mock_urlopen.assert_called_once()
        