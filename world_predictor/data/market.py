"""Market Data Integration.

Fetches real financial data (exchange rates, stock indices) to feed into
simulation as additional economic signals. Uses free APIs.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


# Major stock indices by country
COUNTRY_INDICES = {
    "US": "^GSPC",       # S&P 500
    "CN": "000001.SS",   # Shanghai Composite
    "JP": "^N225",       # Nikkei 225
    "GB": "^FTSE",       # FTSE 100
    "DE": "^GDAXI",      # DAX
    "FR": "^FCHI",       # CAC 40
    "IN": "^BSESN",      # BSE Sensex
    "BR": "^BVSP",       # Bovespa
    "KR": "^KS11",       # KOSPI
    "AU": "^AXJO",       # ASX 200
    "RU": "IMOEX.ME",    # MOEX
}


class MarketDataFetcher:
    """Fetch market data from free APIs."""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._last_fetch: Optional[datetime] = None

    def fetch_exchange_rates(self, base: str = "USD") -> Dict[str, float]:
        """Fetch current exchange rates from free API.

        Returns {currency_code: rate_vs_base}
        """
        try:
            resp = requests.get(
                f"https://open.er-api.com/v6/latest/{base}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("result") == "success":
                rates = data.get("rates", {})
                self._cache["exchange_rates"] = rates
                self._last_fetch = datetime.now()
                return rates
        except Exception as e:
            logger.warning("Exchange rate fetch failed: %s", e)
        return self._cache.get("exchange_rates", {})

    def get_economic_signal(self, country: str, rates: Dict[str, float]) -> Dict[str, float]:
        """Convert market data into economic signals for the simulation.

        Returns normalized signals that can be fed into the engine:
        - currency_strength: 0 to 1 (relative to USD)
        - market_sentiment: -1 to 1 (placeholder for index changes)
        """
        currency_map = {
            "US": "USD", "CN": "CNY", "IN": "INR", "BR": "BRL", "RU": "RUB",
            "JP": "JPY", "DE": "EUR", "GB": "GBP", "FR": "EUR", "KR": "KRW",
            "AU": "AUD", "MX": "MXN", "ID": "IDR", "NG": "NGN", "EG": "EGP",
            "SA": "SAR", "TR": "TRY", "PK": "PKR", "PH": "PHP", "TH": "THB",
        }

        # Baseline rates (approximate historical average for normalization)
        baseline_rates = {
            "USD": 1.0, "CNY": 7.0, "INR": 83.0, "BRL": 5.0, "RUB": 90.0,
            "JPY": 150.0, "EUR": 0.92, "GBP": 0.79, "KRW": 1300.0,
            "AUD": 1.55, "MXN": 17.0, "IDR": 15500.0, "NGN": 1500.0,
            "EGP": 50.0, "SAR": 3.75, "TRY": 30.0, "PKR": 280.0,
            "PHP": 56.0, "THB": 35.0,
        }

        currency = currency_map.get(country, "USD")
        current_rate = rates.get(currency, baseline_rates.get(currency, 1.0))
        baseline = baseline_rates.get(currency, current_rate)

        # Currency strength: lower rate = stronger (for non-USD)
        if currency == "USD":
            strength = 0.5
        else:
            # How much the currency has changed vs baseline
            change_pct = (current_rate - baseline) / max(baseline, 1) * 100
            # Negative change = currency strengthened, positive = weakened
            strength = max(0, min(1, 0.5 - change_pct / 50))

        return {
            "currency_strength": round(strength, 4),
            "currency_code": currency,
            "exchange_rate": current_rate,
        }

    def get_all_signals(self) -> Dict[str, Dict[str, float]]:
        """Fetch rates and return economic signals for all countries."""
        rates = self.fetch_exchange_rates()
        signals = {}
        countries = ["US", "CN", "IN", "BR", "RU", "JP", "DE", "GB", "FR", "KR",
                     "AU", "MX", "ID", "NG", "EG", "SA", "TR", "PK", "PH", "TH"]
        for country in countries:
            signals[country] = self.get_economic_signal(country, rates)
        return signals
