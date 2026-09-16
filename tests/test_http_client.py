import httpx

from app.http_client import SafeHttpClient


def test_safe_http_client_retries_transient_connection_errors(monkeypatch) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectTimeout("temporary timeout", request=request)
        return httpx.Response(200, content=b"recovered", request=request)

    client = SafeHttpClient(timeout=1, interval=0)
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr("app.http_client.time.sleep", lambda _seconds: None)
    try:
        result = client.get("https://www.gazzettaufficiale.it/example")
    finally:
        client.close()

    assert attempts == 2
    assert result.content == b"recovered"
