import json
from django.conf import settings
from openai import OpenAI

from openai import OpenAIError


class SEOOptimizerService:
    """Service to optimize content using OpenAI for SEO purposes."""

    def _get_client():
        return OpenAI(api_key=settings.OPEN_AI_SECRET_KEY)

    @classmethod
    def _send_request(cls, prompt: str, temperature: float) -> dict:
        """Internal helper to send requests to OpenAI and return parsed JSON."""
        try:
            response = cls._get_client().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert SEO content optimizer. "
                            "Always respond in valid JSON format with exactly these keys: "
                            "`optimized_content` (string) and `improvements_done` (list of strings)."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )

            raw_content = response.choices[0].message.content.strip()

            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON returned from model: {raw_content}")

            # validate structure
            if (
                not isinstance(parsed, dict)
                or "optimized_content" not in parsed
                or "improvements_done" not in parsed
                or not isinstance(parsed["improvements_done"], list)
            ):
                raise RuntimeError(f"Unexpected JSON structure: {parsed}")

            return parsed

        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    @classmethod
    def post_analysis_optimize(
        cls,
        content: str,
        keyword: str,
        readability_score: float,
        avg_sentence_length: float,
        issues: dict,
        keyword_density: float,
        word_count: int,
    ) -> dict:
        """Optimize content after analysis using only keyword."""
        if not content or not keyword:
            raise ValueError(
                "Content and keyword are required for post-analysis optimization."
            )

        prompt = f"""
        Optimize this content for SEO with keyword "{keyword}":
        - Maintain natural keyword density (1-3%)
        - Improve readability
        - Add relevant semantic keywords
        - Keep the same tone and style
        - Current Readability score: {readability_score if readability_score else 'Unknown, you should calculate this youreself as an SEO expert'}
        - Current Keyword Density: {keyword_density if keyword_density else 'Unknown, you should calculate this youreself as an SEO expert'}
        - Current Average sentence length: {avg_sentence_length if avg_sentence_length else 'Unknown, you should calculate this youreself as an SEO expert'}
        - Potential Initial Issues Found: {issues if issues else 'Unknown, you should check this youreself as an SEO expert'}
        - Current Word Count: {word_count if word_count else 'Unknown, you should calculate this youreself as an SEO expert'}
        Return ONLY valid JSON like this:
        {{
            "optimized_content": "string",
            "improvements_done": ["string", "string", ...]
        }}

        Content:
        {content}
        """
        return cls._send_request(prompt, temperature=0.5)

    @classmethod
    def optimize(
        cls, content: str, keyword: str, tone: str, target_length: int
    ) -> dict:
        """Optimize content with custom tone and target length."""
        if not content or not keyword or not tone or not target_length:
            raise ValueError("Content, keyword, tone, and target length are required.")

        prompt = f"""
        Optimize this content for SEO with keyword "{keyword}":
        - Maintain natural keyword density (1-3%)
        - Improve readability
        - Add relevant semantic keywords
        - Keep the same tone and style
        - Tone: {tone}
        - Target length: {target_length} words
        Return ONLY valid JSON like this:
        {{
            "optimized_content": "string",
            "improvements_done": ["string", "string", ...]
        }}

        Content:
        {content}
        """
        return cls._send_request(prompt, temperature=0.5)
