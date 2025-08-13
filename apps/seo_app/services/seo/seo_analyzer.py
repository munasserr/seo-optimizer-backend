from bs4 import BeautifulSoup
import re
import textstat
from .constants import ISSUE_DEFINITIONS


class SEOAnalyzer:
    """SEO Analyzer Service to analyze SEO content."""

    VALID_INPUT_TYPES = ["html", "content"]

    SEVERITY_PENALTIES = {"low": 3, "medium": 7, "high": 15}

    def __init__(self, content: str, target_keyword: str, input_type: str):
        if not content or not content.strip():
            raise ValueError("SEOAnalyzer requires non-empty content.")
        if not target_keyword or not target_keyword.strip():
            raise ValueError("SEOAnalyzer requires a target keyword.")
        if not input_type or input_type.lower().strip() not in self.VALID_INPUT_TYPES:
            raise ValueError(
                f"Invalid input_type. Must be one of {self.VALID_INPUT_TYPES}"
            )

        self.content = content
        self.target_keyword = target_keyword.lower().strip()
        self.input_type = input_type.lower().strip()

    # text & metric utilities
    def _get_text_only(self):
        """Extract plain text from HTML or return content directly."""
        if self.input_type == "html":
            soup = BeautifulSoup(self.content, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        return self.content

    def count_words(self):
        return len(self._get_text_only().split())

    def calculate_keyword_density(self):
        words = self._get_text_only().lower().split()
        if not words:
            return 0
        keyword_count = words.count(self.target_keyword)
        return round((keyword_count / len(words)) * 100, 2)

    def average_sentence_length(self):
        text = self._get_text_only()
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        return round(sum(len(s.split()) for s in sentences) / len(sentences), 2)

    def calculate_readability(self):
        return round(textstat.flesch_reading_ease(self._get_text_only()), 2)

    # html specific utilities
    def extract_headings(self):
        if self.input_type != "html":
            return {}
        soup = BeautifulSoup(self.content, "html.parser")
        return {
            "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
            "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
            "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
        }

    def check_meta_description(self):
        if self.input_type != "html":
            return None
        soup = BeautifulSoup(self.content, "html.parser")
        meta_tag = soup.find("meta", attrs={"name": "description"})
        return bool(meta_tag and meta_tag.get("content"))

    # issue detection
    def generate_issues(self):
        issues_found = {}
        density = self.calculate_keyword_density()

        # keyword Density
        if density < 0.5:
            issues_found["keyword_density_low"] = ISSUE_DEFINITIONS[
                "keyword_density_low"
            ]
        elif density > 5:
            issues_found["keyword_density_high"] = ISSUE_DEFINITIONS[
                "keyword_density_high"
            ]

        # HTML checks
        if self.input_type == "html":
            headings = self.extract_headings()
            if not headings.get("h1"):
                issues_found["no_h1_tag"] = ISSUE_DEFINITIONS["no_h1_tag"]

            if not self.check_meta_description():
                issues_found["missing_meta_description"] = ISSUE_DEFINITIONS[
                    "missing_meta_description"
                ]

            # check for missing subheadings
            if not headings.get("h2") and not headings.get("h3"):
                issues_found["missing_subheadings"] = ISSUE_DEFINITIONS[
                    "missing_subheadings"
                ]

        # readability check
        if self.calculate_readability() < 50:
            issues_found["readability_poor"] = ISSUE_DEFINITIONS["readability_poor"]

        return issues_found

    def calculate_mock_seo_score(self):
        """Calculate SEO score based on issues and severity."""
        score = 100
        issues = self.generate_issues()

        for issue_key in issues:
            severity = ISSUE_DEFINITIONS.get(issue_key, {}).get("severity", "low")
            penalty = self.SEVERITY_PENALTIES.get(severity)
            score -= penalty

        return max(0, min(100, score))  # keep it between 0 and 100

    # final analysis
    def analyze(self):
        return {
            "input_type": self.input_type,
            "word_count": self.count_words(),
            "keyword_density": self.calculate_keyword_density(),
            "headings": self.extract_headings() if self.input_type == "html" else {},
            "has_meta_description": (
                self.check_meta_description() if self.input_type == "html" else None
            ),
            "readability_score": self.calculate_readability(),
            "avg_sentence_length": self.average_sentence_length(),
            "seo_score": self.calculate_mock_seo_score(),
            "issues": self.generate_issues(),
        }
