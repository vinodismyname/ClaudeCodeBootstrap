"""
Perplexity API client for research integration.
"""

import requests
import logging
from typing import Dict, Any, Optional


class PerplexityClient:
    """Client for interacting with Perplexity API."""

    def __init__(self, api_key: str):
        """
        Initialize the Perplexity client.

        Args:
            api_key: Perplexity API key
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"

    def query(self, question: str, focus: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the Perplexity API.

        Args:
            question: The question to ask
            focus: Optional focus area for the query

        Returns:
            Dictionary containing the API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [{"role": "user", "content": question}]

        if focus:
            messages.insert(
                0, {"role": "system", "content": f"Focus on this aspect: {focus}"}
            )

        data = {"model": "sonar-pro", "messages": messages}

        self.logger.debug(f"Querying Perplexity API: {question}")

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", headers=headers, json=data
            )

            if response.status_code != 200:
                self.logger.error(
                    f"Perplexity API error: {response.status_code} - {response.text}"
                )
                raise Exception(
                    f"Perplexity API error: {response.status_code} - {response.text}"
                )

            self.logger.debug("Received response from Perplexity API")
            return response.json()
        except Exception as e:
            self.logger.error(f"Error querying Perplexity API: {e}")
            raise
