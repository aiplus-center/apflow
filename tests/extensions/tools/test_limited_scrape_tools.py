import pytest
from typing import Dict
from unittest.mock import patch
from apflow.extensions.tools.limited_scrape_tools import (
    LimitedScrapeWebsiteTool,
    LimitedScrapeWebsiteInputSchema,
)


class DummyResponse:
    def __init__(self, text: str, url: str = "http://test.com", status_code: int = 200):
        self.text = text
        self.content = text.encode("utf-8")
        self.url = url
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise Exception("HTTP error")


@pytest.fixture
def html_with_metadata() -> str:
    return """
    <html>
        <head>
            <title>Test Title</title>
            <meta name="description" content="Test Description">
        </head>
        <body>
            <main>This is the main content. It should be extracted.</main>
            <a href="https://twitter.com/testuser">Twitter</a>
        </body>
    </html>
    """


def test_extract_social_media_links(html_with_metadata: str) -> None:
    from bs4 import BeautifulSoup

    tool = LimitedScrapeWebsiteTool()
    soup = BeautifulSoup(html_with_metadata, "html.parser")
    links: Dict[str, str] = tool._extract_social_media_links(soup, "http://test.com")
    assert "twitter" in links
    assert links["twitter"].startswith("https://twitter.com/")


def test_extract_content_by_soup(html_with_metadata: str) -> None:
    tool = LimitedScrapeWebsiteTool()
    response = DummyResponse(html_with_metadata)
    content = tool.extract_content_by_soup(response)
    assert "This is the main content" in content


@patch("apflow.extensions.tools.limited_scrape_tools.requests.get")
def test_run_success(mock_get, html_with_metadata: str) -> None:
    tool = LimitedScrapeWebsiteTool()
    mock_get.return_value = DummyResponse(html_with_metadata)
    # Patch extract_content to return predictable content, so test does not depend on trafilatura
    with patch.object(
        LimitedScrapeWebsiteTool,
        "extract_content",
        return_value="This is the main content. It should be extracted.",
    ):
        result = tool._run("http://test.com")
    assert "Test Title" in result
    assert "Test Description" in result
    assert "This is the main content" in result
    assert "twitter" in result.lower()


@patch("apflow.extensions.tools.limited_scrape_tools.requests.get")
def test_run_request_exception(mock_get) -> None:
    tool = LimitedScrapeWebsiteTool()
    mock_get.side_effect = Exception("Network error")
    result = tool._run("http://badurl.com")
    assert "Error: Could not access" in result or "Error: Failed to scrape" in result


def test_input_schema_validation() -> None:
    # Valid input
    schema = LimitedScrapeWebsiteInputSchema(
        website_url="http://test.com",
        max_chars=1000,
        extract_metadata=True,
        headers={"X-Test": "1"},
    )
    assert schema.website_url == "http://test.com"
    assert schema.max_chars == 1000
    assert schema.extract_metadata is True
    assert schema.headers == {"X-Test": "1"}


def test_content_truncation(html_with_metadata: str) -> None:
    tool = LimitedScrapeWebsiteTool()
    # Patch extract_content to return a long string using patch.object, to avoid pydantic dynamic attribute error
    with patch.object(LimitedScrapeWebsiteTool, "extract_content", return_value="A. " * 3000):
        with patch("apflow.extensions.tools.limited_scrape_tools.requests.get") as mock_get:
            mock_get.return_value = DummyResponse(html_with_metadata)
            result = tool._run("http://test.com", max_chars=100)
            # Ensure the result is truncated as expected
            assert len(result) <= 100 or result.endswith("...")


def test_real_website_scrape() -> None:
    tool = LimitedScrapeWebsiteTool()
    # Using a simple real website for testing
    result = tool._run("https://flow-docs.aiperceivable.com", max_chars=10000)
    print("=== Scrape Result ===")
    print(result)
