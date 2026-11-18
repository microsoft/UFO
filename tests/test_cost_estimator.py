# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for BaseService.get_cost_estimator.

prices.yaml rows win. Models that prices.yaml does not list are priced with the
optional llm-prices package, and cost 0 when it is not installed.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from ufo.llm import base
from ufo.llm.base import BaseService

try:
    import llm_prices
except ImportError:
    llm_prices = None

PRICES_YAML = Path(__file__).resolve().parents[1] / "config" / "ufo" / "prices.yaml"


class _Service(BaseService):
    def __init__(self):
        pass

    def chat_completion(self, *args, **kwargs):
        pass


class TestCostEstimator(unittest.TestCase):
    def setUp(self):
        self.service = _Service()
        with open(PRICES_YAML, "r", encoding="utf-8") as f:
            self.prices = yaml.safe_load(f)["PRICES"]

    def cost(self, api_type, model, prompt_tokens, completion_tokens, prices=None):
        return self.service.get_cost_estimator(
            api_type,
            model,
            self.prices if prices is None else prices,
            prompt_tokens,
            completion_tokens,
        )

    def test_yaml_row_takes_precedence(self):
        prices = {"openai/gpt-5": {"input": 0.5, "output": 1.0}}
        self.assertAlmostEqual(self.cost("openai", "gpt-5", 1000, 1000, prices), 1.5)

    def test_shipped_rows_match_list_prices(self):
        # 1M input + 1M output tokens, in USD
        self.assertAlmostEqual(
            self.cost("claude", "claude-3-5-sonnet-20241022", 1_000_000, 1_000_000), 18.0
        )
        self.assertAlmostEqual(
            self.cost("claude", "claude-3-5-sonnet", 1_000_000, 1_000_000), 18.0
        )
        self.assertAlmostEqual(
            self.cost("gemini", "gemini-2.5-pro-preview-03-25", 1_000_000, 0), 1.25
        )
        self.assertAlmostEqual(self.cost("openai", "gpt-4o", 1_000_000, 1_000_000), 12.5)

    def test_unknown_model_without_llm_prices_is_zero(self):
        with patch.object(base, "llm_prices", None):
            self.assertEqual(self.cost("openai", "gpt-5", 1000, 1000), 0)

    def test_unknown_model_is_zero(self):
        self.assertEqual(self.cost("openai", "not-a-real-model", 1000, 1000), 0)
        self.assertEqual(self.cost("qwen", "qwen-max", 1000, 1000), 0)

    @unittest.skipIf(llm_prices is None, "llm-prices not installed")
    def test_models_missing_from_yaml_are_priced(self):
        cases = [
            ("openai", "gpt-5", "openai"),
            ("aoai", "gpt-5", "openai"),
            ("azure_ad", "gpt-4.1", "openai"),
            ("claude", "claude-sonnet-4-6", "anthropic"),
            ("gemini", "gemini-2.5-pro", "google"),
        ]
        for api_type, model, provider in cases:
            with self.subTest(api_type=api_type, model=model):
                expected = llm_prices.lookup_provider(provider, model).cost(12_000, 800)
                cost = self.cost(api_type, model, 12_000, 800)
                self.assertGreater(cost, 0)
                self.assertAlmostEqual(cost, expected)

    @unittest.skipIf(llm_prices is None, "llm-prices not installed")
    def test_claude_sonnet_4_6_cost(self):
        # $3 / $15 per 1M tokens: 12,000 in + 800 out = 0.036 + 0.012
        self.assertAlmostEqual(self.cost("claude", "claude-sonnet-4-6", 12_000, 800), 0.048)


if __name__ == "__main__":
    unittest.main()
