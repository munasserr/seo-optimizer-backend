import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from bs4 import BeautifulSoup

from apps.seo_app.services.seo.seo_analyzer import SEOAnalyzer
from apps.seo_app.services.ai.seo_ai_service import SEOOptimizerService
from apps.seo_app.services.common.extract_html import (
    extract_html,
    extract_text_from_html,
)


class TestSEOAnalyzer:
    """Test SEO analyzer functionality."""

    @pytest.mark.parametrize("input_type", ["html", "content"])
    def test_seo_analyzer_initialization(self, input_type):
        """Test SEO analyzer can be initialized with different input types."""
        content = "This is test content with keyword analysis."
        keyword = "test keyword"

        analyzer = SEOAnalyzer(content, keyword, input_type)

        assert analyzer.content == content
        assert analyzer.target_keyword == "test keyword"  # Should be lowercased
        assert analyzer.input_type == input_type

    @pytest.mark.parametrize(
        "content,keyword,input_type,expected_error",
        [
            ("", "keyword", "content", "non-empty content"),
            ("content", "", "content", "target keyword"),
            ("content", "keyword", "invalid", "Invalid input_type"),
            (None, "keyword", "content", "non-empty content"),
            ("content", None, "content", "target keyword"),
        ],
    )
    def test_seo_analyzer_validation(
        self, content, keyword, input_type, expected_error
    ):
        """Test SEO analyzer input validation."""
        with pytest.raises(ValueError, match=expected_error):
            SEOAnalyzer(content, keyword, input_type)

    def test_word_count_calculation(self):
        """Test word count calculation."""
        content = "This is a test content with exactly ten words here."
        analyzer = SEOAnalyzer(content, "test", "content")

        assert analyzer.count_words() == 10

    @pytest.mark.parametrize(
        "content,keyword,expected_density",
        [
            ("test keyword test", "test", 66.67),  # 2 out of 3 words
            ("keyword test keyword test keyword", "keyword", 60.0),  # 3 out of 5 words
            ("no matching words here", "missing", 0.0),  # 0 matches
            ("single", "single", 100.0),  # 1 out of 1 word
        ],
    )
    def test_keyword_density_calculation(self, content, keyword, expected_density):
        """Test keyword density calculation with various scenarios."""
        analyzer = SEOAnalyzer(content, keyword, "content")

        assert analyzer.calculate_keyword_density() == expected_density

    def test_average_sentence_length(self):
        """Test average sentence length calculation."""
        content = "First sentence has four words. Second sentence has exactly five words here. Third sentence has three words."
        analyzer = SEOAnalyzer(content, "test", "content")

        assert analyzer.average_sentence_length() == 5.67

    def test_readability_calculation(self):
        """Test readability score calculation."""
        content = (
            "This is a simple sentence. It should have a decent readability score."
        )
        analyzer = SEOAnalyzer(content, "test", "content")

        readability = analyzer.calculate_readability()
        assert isinstance(readability, float)
        assert 0 <= readability <= 100

    def test_html_heading_extraction(self):
        """Test HTML heading extraction."""
        html_content = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading One</h2>
                <h2>Subheading Two</h2>
                <h3>Sub-subheading</h3>
                <p>Regular content</p>
            </body>
        </html>
        """
        analyzer = SEOAnalyzer(html_content, "test", "html")

        headings = analyzer.extract_headings()

        assert headings["h1"] == ["Main Heading"]
        assert headings["h2"] == ["Subheading One", "Subheading Two"]
        assert headings["h3"] == ["Sub-subheading"]

    def test_meta_description_check(self):
        """Test meta description detection."""
        html_with_meta = """
        <html>
            <head>
                <meta name="description" content="This is a meta description">
            </head>
            <body>Content here</body>
        </html>
        """
        html_without_meta = "<html><body>Content without meta</body></html>"

        analyzer_with = SEOAnalyzer(html_with_meta, "test", "html")
        analyzer_without = SEOAnalyzer(html_without_meta, "test", "html")

        assert analyzer_with.check_meta_description() is True
        assert analyzer_without.check_meta_description() is False

    def test_content_type_meta_description_returns_none(self):
        """Test that content type returns None for meta description check."""
        analyzer = SEOAnalyzer("Regular content", "test", "content")
        assert analyzer.check_meta_description() is None

    @pytest.mark.parametrize(
        "keyword_density,expected_issue",
        [
            (0.3, "keyword_density_low"),  # Too low
            (6.0, "keyword_density_high"),  # Too high
            (2.5, None),  # Just right
        ],
    )
    def test_keyword_density_issues(self, keyword_density, expected_issue):
        """Test keyword density issue detection."""
        with patch.object(
            SEOAnalyzer, "calculate_keyword_density", return_value=keyword_density
        ):
            analyzer = SEOAnalyzer("test content", "test", "content")
            issues = analyzer.generate_issues()

            if expected_issue:
                assert expected_issue in issues
            else:
                assert "keyword_density_low" not in issues
                assert "keyword_density_high" not in issues

    def test_seo_score_calculation(self):
        """Test SEO score calculation based on issues."""
        analyzer = SEOAnalyzer("test content", "test", "content")

        # Mock various methods to control the score
        with patch.object(analyzer, "generate_issues", return_value={}):
            score = analyzer.calculate_mock_seo_score()
            assert score == 100  # No issues = perfect score

        # Test with issues
        issues = {
            "keyword_density_low": {"severity": "medium"},  # -7 points
            "readability_poor": {"severity": "medium"},  # -7 points
        }
        with patch.object(analyzer, "generate_issues", return_value=issues):
            score = analyzer.calculate_mock_seo_score()
            assert score == 86  # 100 - 7 - 7 = 86

    def test_full_analysis_content_type(self):
        """Test complete analysis for content type."""
        content = "This is test content with test keyword for analysis test."
        analyzer = SEOAnalyzer(content, "test", "content")

        result = analyzer.analyze()

        assert result["input_type"] == "content"
        assert isinstance(result["word_count"], int)
        assert isinstance(result["keyword_density"], float)
        assert isinstance(result["readability_score"], float)
        assert isinstance(result["avg_sentence_length"], float)
        assert isinstance(result["seo_score"], (int, float))
        assert isinstance(result["issues"], dict)
        assert result["headings"] == {}  # Empty for content type
        assert result["has_meta_description"] is None  # None for content type

    def test_full_analysis_html_type(self):
        """Test complete analysis for HTML type."""
        html_content = """
        <html>
            <head>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Test Heading</h1>
                <p>This is test content with test keyword.</p>
            </body>
        </html>
        """
        analyzer = SEOAnalyzer(html_content, "test", "html")

        result = analyzer.analyze()

        assert result["input_type"] == "html"
        assert isinstance(result["headings"], dict)
        assert result["has_meta_description"] is True


class TestSEOOptimizerService:
    """Test SEO optimizer AI service with mocked OpenAI calls."""

    def test_get_client(self):
        """Test OpenAI client initialization."""
        with patch("apps.seo_app.services.ai.seo_ai_service.OpenAI") as mock_openai:
            SEOOptimizerService._get_client()
            mock_openai.assert_called_once()

    @patch("apps.seo_app.services.ai.seo_ai_service.SEOOptimizerService._get_client")
    def test_send_request_success(self, mock_get_client):
        """Test successful API request to OpenAI."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "optimized_content": "Optimized content here",
                "improvements_done": ["Added keywords", "Improved readability"],
            }
        )

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = SEOOptimizerService._send_request("test prompt", 0.5)

        assert result["optimized_content"] == "Optimized content here"
        assert len(result["improvements_done"]) == 2
        mock_client.chat.completions.create.assert_called_once()

    @patch("apps.seo_app.services.ai.seo_ai_service.SEOOptimizerService._get_client")
    def test_send_request_invalid_json(self, mock_get_client):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Invalid JSON returned from model"):
            SEOOptimizerService._send_request("test prompt", 0.5)

    @patch("apps.seo_app.services.ai.seo_ai_service.SEOOptimizerService._get_client")
    def test_send_request_missing_keys(self, mock_get_client):
        """Test handling of response with missing required keys."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "optimized_content": "Content here"
                # Missing improvements_done key
            }
        )

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Unexpected JSON structure"):
            SEOOptimizerService._send_request("test prompt", 0.5)

    @patch("apps.seo_app.services.ai.seo_ai_service.SEOOptimizerService._send_request")
    def test_post_analysis_optimize(self, mock_send_request):
        """Test post-analysis optimization."""
        mock_send_request.return_value = {
            "optimized_content": "Optimized content with keyword",
            "improvements_done": ["Enhanced keyword density", "Improved structure"],
        }

        result = SEOOptimizerService.post_analysis_optimize(
            content="Original content",
            keyword="test keyword",
            readability_score=65.0,
            avg_sentence_length=15.5,
            issues={"keyword_density_low": {"severity": "medium"}},
            keyword_density=0.5,
            word_count=50,
        )

        assert result["optimized_content"] == "Optimized content with keyword"
        assert len(result["improvements_done"]) == 2
        mock_send_request.assert_called_once()

        # Verify the prompt contains key information
        call_args = mock_send_request.call_args[0]
        prompt = call_args[0]
        assert "test keyword" in prompt
        assert "65.0" in prompt or "65" in prompt

    @pytest.mark.parametrize("missing_param", ["content", "keyword"])
    def test_post_analysis_optimize_validation(self, missing_param):
        """Test validation of required parameters."""
        params = {
            "content": "Test content",
            "keyword": "test keyword",
            "readability_score": 65.0,
            "avg_sentence_length": 15.5,
            "issues": {},
            "keyword_density": 2.0,
            "word_count": 50,
        }
        params[missing_param] = None

        with pytest.raises(ValueError):
            SEOOptimizerService.post_analysis_optimize(**params)

    @patch("apps.seo_app.services.ai.seo_ai_service.SEOOptimizerService._send_request")
    def test_optimize(self, mock_send_request):
        """Test content optimization."""
        mock_send_request.return_value = {
            "optimized_content": "Professional optimized content for keyword",
            "improvements_done": ["Adjusted tone", "Reached target length"],
        }

        result = SEOOptimizerService.optimize(
            content="Original content",
            keyword="test keyword",
            tone="professional",
            target_length=500,
        )

        assert (
            result["optimized_content"] == "Professional optimized content for keyword"
        )
        assert len(result["improvements_done"]) == 2
        mock_send_request.assert_called_once()

        # Verify the prompt contains parameters
        call_args = mock_send_request.call_args[0]
        prompt = call_args[0]
        assert "test keyword" in prompt
        assert "professional" in prompt
        assert "500" in prompt

    @pytest.mark.parametrize(
        "missing_param", ["content", "keyword", "tone", "target_length"]
    )
    def test_optimize_validation(self, missing_param):
        """Test validation of required parameters for optimization."""
        params = {
            "content": "Test content",
            "keyword": "test keyword",
            "tone": "professional",
            "target_length": 500,
        }
        params[missing_param] = None

        with pytest.raises(ValueError):
            SEOOptimizerService.optimize(**params)


class TestHTMLExtraction:
    """Test HTML extraction utilities."""

    @patch("apps.seo_app.services.common.extract_html.requests.get")
    def test_extract_html_success(self, mock_get):
        """Test successful HTML extraction."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <head><title>Test</title></head>
            <body>
                <script>alert('remove me');</script>
                <h1>Keep this heading</h1>
                <p>Keep this content</p>
                <footer>Remove footer</footer>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = extract_html("https://example.com")

        # Should contain allowed tags but not scripts/footer
        assert "Keep this heading" in result
        assert "Keep this content" in result
        assert "alert('remove me')" not in result
        assert "Remove footer" not in result
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    @patch("apps.seo_app.services.common.extract_html.requests.get")
    def test_extract_text_from_html_success(self, mock_get):
        """Test successful text extraction from HTML."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <p>This is paragraph content.</p>
                <script>console.log('ignore');</script>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = extract_text_from_html("https://example.com")

        assert "Main Heading" in result
        assert "This is paragraph content." in result
        assert "console.log" not in result
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    @patch("apps.seo_app.services.common.extract_html.requests.get")
    def test_extract_html_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            extract_html("https://example.com")

    def test_html_cleaning_removes_unwanted_tags(self):
        """Test that unwanted tags are properly removed."""
        with patch(
            "apps.seo_app.services.common.extract_html.requests.get"
        ) as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <html>
                <body>
                    <h1>Keep this</h1>
                    <script>remove this</script>
                    <style>remove this too</style>
                    <noscript>remove this</noscript>
                    <iframe>remove this</iframe>
                    <header>remove this</header>
                    <footer>remove this</footer>
                    <nav>remove this</nav>
                    <p>Keep this paragraph</p>
                </body>
            </html>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = extract_html("https://example.com")

            assert "Keep this" in result
            assert "Keep this paragraph" in result
            assert "remove this" not in result
