import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict
import pycountry

class Visualizer:
    def __init__(self):
        self.colors = {
            "positive": "#2ecc71",
            "negative": "#e74c3c",
            "neutral": "#f39c12"
        }

    def _get_country_centroid(self, country_code: str):
        # Placeholder mapping
        centroids = {
            "US": (37.0902, -95.7129),
            "CN": (35.8617, 104.1954),
            "IN": (20.5937, 78.9629),
            "BR": (-14.2350, -51.9253),
            "RU": (61.5240, 105.3188),
            "JP": (36.2048, 138.2529),
            "DE": (51.1657, 10.4515),
            "GB": (55.3781, -3.4360),
            "FR": (46.2276, 2.2137),
            "KR": (35.9078, 127.7669),
            "AU": (-25.2744, 133.7751),
            "MX": (23.6345, -102.5528),
            "ID": (-0.7893, 113.9213),
            "NG": (9.0820, 8.6753),
            "EG": (26.8206, 30.8025),
            "SA": (23.8859, 45.0792),
            "TR": (38.9637, 35.2433),
            "PK": (30.3753, 69.3451),
            "PH": (12.8797, 121.7740),
            "TH": (15.8700, 100.9925),
        }
        return centroids.get(country_code, (0, 0))

    def _get_sentiment_color(self, score: float) -> str:
        if score > 0.6: return self.colors["positive"]
        if score < 0.4: return self.colors["negative"]
        return self.colors["neutral"]

    def create_3d_globe(self, agent_data: List[Dict]) -> go.Figure:
        """Create a 3D globe visualization"""
        fig = go.Figure()

        # Add country data
        for agent in agent_data:
            if pycountry.countries.get(alpha_2=agent['location']):
                lat, lon = self._get_country_centroid(agent['location'])
                
                fig.add_trace(go.Scattergeo(
                    lat=[lat],
                    lon=[lon],
                    marker=dict(
                        size=5,
                        color=self._get_sentiment_color(agent['behavior']['optimism']),
                        opacity=0.6
                    ),
                    name=agent['location']
                ))

        fig.update_geos(
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor="rgb(107, 107, 107)"
        )

        fig.update_layout(height=600, margin={"r":0,"t":0,"l":0,"b":0})
        return fig

    def create_metrics_dashboard(self, metrics: Dict[str, float]) -> go.Figure:
        """Create a metrics dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Economic Sentiment", "Social Cohesion", "Political Stability", "Average Optimism"),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )

        indicators = [
            ("Economic Sentiment", metrics.get("economic_sentiment", 0), self.colors["neutral"]),
            ("Social Cohesion", metrics.get("social_cohesion", 0), self.colors["neutral"]),
            ("Political Stability", metrics.get("political_stability", 0), self.colors["neutral"]),
            ("Average Optimism", metrics.get("average_optimism", 0), self.colors["neutral"])
        ]

        for i, (title, value, color) in enumerate(indicators):
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    title={"text": title},
                    gauge={
                        'axis': {'range': [0, 1]},
                        'bar': {'color': color}
                    }
                ), row=(i//2)+1, col=(i%2)+1
            )

        return fig

    def create_trend_chart(self, daily_data: List[Dict]) -> go.Figure:
        """Create a trend chart for simulation data"""
        df = pd.DataFrame(daily_data)

        fig = go.Figure()

        if 'day' in df.columns:
            if 'metrics.economic_sentiment' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['day'],
                    y=df['metrics.economic_sentiment'],
                    name='Economic Sentiment',
                    line=dict(color=self.colors['neutral'])
                ))
            if 'metrics.social_cohesion' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['day'],
                    y=df['metrics.social_cohesion'],
                    name='Social Cohesion',
                    line=dict(color=self.colors['neutral'])
                ))

        fig.update_layout(
            title='Daily Simulation Trends',
            xaxis_title='Day',
            yaxis_title='Score'
        )
        return fig
