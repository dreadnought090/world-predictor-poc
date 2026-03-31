import numpy as np
import pytest
from collections import Counter
from world_predictor.data.agents import AgentGenerator, Agent
from world_predictor.data.news import NewsSource, NewsItem
from world_predictor.simulation.engine import SimulationEngine, CountryEngine
from world_predictor.simulation.models import TrustModel, ReactionTypes, SimulationState


@pytest.fixture
def us_agents():
    gen = AgentGenerator()
    return gen.generate_agents_for_country("US", 500)


@pytest.fixture
def country_engine(us_agents):
    return CountryEngine("US", us_agents)


@pytest.fixture
def engine(us_agents):
    return SimulationEngine(agents=us_agents)


def _make_news(title="Test news", politics=0.0, credibility=0.8, impact=0.5, region="US", category="GENERAL"):
    source = NewsSource(title.split()[0], politics, credibility)
    return NewsItem(title=title, source=source, category=category,
                    content="Test content", url="", region=region, impact=impact)


# ---------------------------------------------------------------------------
# TrustModel
# ---------------------------------------------------------------------------

class TestTrustModel:
    @pytest.fixture
    def trust_model(self):
        return TrustModel()

    @pytest.fixture
    def base_agent(self):
        return Agent(
            id="test_1",
            demographics={"age": "35", "gender": "male", "race": "white",
                          "religion": "christian", "education": "bachelor", "iq": "100"},
            economic={"income": 50000, "financial_stability": 0.5, "career_progression": 0.5},
            behavior={"optimism": 0.5, "risk_aversion": 0.5, "trust_institutions": 0.5},
            location="US",
            politics=0.0,
        )

    def test_trust_returns_float_between_0_and_1(self, trust_model, base_agent):
        source = NewsSource("Reuters", 0.0, 0.9)
        trust = trust_model.calculate_trust(base_agent, source)
        assert 0.0 <= trust <= 1.0

    def test_aligned_politics_increases_trust(self, trust_model, base_agent):
        aligned = NewsSource("Aligned", 0.0, 0.8)
        misaligned = NewsSource("Misaligned", 0.8, 0.8)
        base_agent.politics = 0.0
        trust_aligned = trust_model.calculate_trust(base_agent, aligned)
        trust_misaligned = trust_model.calculate_trust(base_agent, misaligned)
        assert trust_aligned > trust_misaligned

    def test_high_credibility_increases_trust(self, trust_model, base_agent):
        high_cred = NewsSource("Good", 0.0, 0.95)
        low_cred = NewsSource("Bad", 0.0, 0.3)
        t_high = trust_model.calculate_trust(base_agent, high_cred)
        t_low = trust_model.calculate_trust(base_agent, low_cred)
        assert t_high > t_low

    def test_high_iq_weighs_credibility_more(self, trust_model):
        high_iq = Agent(id="hi", demographics={"iq": "130", "age": "35", "gender": "m",
                        "race": "w", "religion": "c", "education": "master"},
                        economic={"income": 50000, "financial_stability": 0.5, "career_progression": 0.5},
                        behavior={"optimism": 0.5, "risk_aversion": 0.5, "trust_institutions": 0.5},
                        location="US", politics=-0.5)
        low_iq = Agent(id="lo", demographics={"iq": "75", "age": "35", "gender": "m",
                       "race": "w", "religion": "c", "education": "high_school"},
                       economic={"income": 30000, "financial_stability": 0.4, "career_progression": 0.3},
                       behavior={"optimism": 0.5, "risk_aversion": 0.5, "trust_institutions": 0.5},
                       location="US", politics=-0.5)
        source = NewsSource("WSJ", 0.5, 0.9)
        t_high = trust_model.calculate_trust(high_iq, source)
        t_low = trust_model.calculate_trust(low_iq, source)
        assert t_high > t_low

    def test_determine_reaction_returns_valid_type(self, trust_model, base_agent):
        news = _make_news()
        reaction = trust_model.determine_reaction(base_agent, news, 0.5)
        assert reaction in ReactionTypes.ALL


class TestReactionTypes:
    def test_all_types_defined(self):
        assert len(ReactionTypes.ALL) == 5
        assert "SUPPORT" in ReactionTypes.ALL
        assert "FEAR" in ReactionTypes.ALL


# ---------------------------------------------------------------------------
# CountryEngine (single-country level)
# ---------------------------------------------------------------------------

class TestCountryEngine:
    def test_process_day_increments_day(self, country_engine):
        news = [_make_news()]
        result = country_engine.process_day(news)
        assert result["day"] == 1
        result2 = country_engine.process_day(news)
        assert result2["day"] == 2

    def test_process_day_returns_expected_keys(self, country_engine):
        news = [_make_news()]
        result = country_engine.process_day(news)
        assert "day" in result
        assert "metrics" in result
        assert "consensus" in result
        assert "reactions" in result
        assert "country" in result

    def test_metrics_have_expected_fields(self, country_engine):
        result = country_engine.process_day([_make_news()])
        metrics = result["metrics"]
        for key in ["economic_sentiment", "social_cohesion", "political_stability",
                     "average_optimism", "average_risk_aversion", "revolution_risk"]:
            assert key in metrics

    def test_reactions_summary(self, country_engine):
        result = country_engine.process_day([_make_news()])
        reactions = result["reactions"]
        assert reactions["total_agents"] == 500
        assert "distribution" in reactions
        assert "percentages" in reactions
        assert reactions["dominant"] in ReactionTypes.ALL
        total = sum(reactions["distribution"].values())
        assert total == 500

    def test_consensus_has_reaction_distribution(self, country_engine):
        result = country_engine.process_day([_make_news()])
        consensus = result["consensus"]
        assert "reaction_distribution" in consensus
        dist = consensus["reaction_distribution"]
        assert abs(sum(dist.values()) - 1.0) < 0.01

    def test_empty_news_still_works(self, country_engine):
        result = country_engine.process_day([])
        assert result["day"] == 1
        assert result["reactions"]["total_agents"] >= 0

    def test_revolution_risk_exists(self, country_engine):
        result = country_engine.process_day([_make_news(impact=0.9)])
        assert "revolution_risk" in result["metrics"]
        assert 0.0 <= result["metrics"]["revolution_risk"] <= 1.0


# ---------------------------------------------------------------------------
# SimulationEngine (multi-country orchestrator)
# ---------------------------------------------------------------------------

class TestSimulationEngine:
    def test_initial_state(self, engine):
        assert len(engine.engines) >= 1
        assert "US" in engine.engines
        assert len(engine.agents) == 500

    def test_process_day_returns_dict_of_countries(self, engine):
        news = [_make_news()]
        results = engine.process_day(news)
        assert isinstance(results, dict)
        assert "US" in results
        assert results["US"]["day"] == 1

    def test_get_predictions_real_data(self, engine):
        pred = engine.get_predictions("US")
        assert pred["country"] == "US"
        assert "metrics" in pred
        assert pred["metrics"]["economic_sentiment"] > 0

    def test_get_all_predictions(self, engine):
        preds = engine.get_all_predictions()
        assert "US" in preds

    def test_simulate_batch(self, engine):
        news = [_make_news()]
        results = engine.simulate_batch(news, days=3)
        assert len(results) == 3

    def test_bad_news_increases_fear(self):
        gen = AgentGenerator()
        agents1 = gen.generate_agents_for_country("US", 500)
        agents2 = [Agent(id=a.id, demographics=dict(a.demographics),
                         economic=dict(a.economic), behavior=dict(a.behavior),
                         location=a.location, politics=a.politics) for a in agents1]

        e1 = CountryEngine("US", agents1)
        e2 = CountryEngine("US", agents2)

        r_bad = e1.process_day([_make_news("Crisis alert", impact=0.95)])
        r_mild = e2.process_day([_make_news("Minor update", impact=0.1)])

        assert r_bad["reactions"]["distribution"]["FEAR"] >= r_mild["reactions"]["distribution"]["FEAR"]


class TestMultiDaySimulation:
    def test_sustained_bad_news_drops_optimism(self):
        gen = AgentGenerator()
        agents = gen.generate_agents_for_country("US", 300)
        engine = CountryEngine("US", agents)

        initial_optimism = np.mean([a.behavior["optimism"] for a in agents])

        bad_news = [
            _make_news("Market crash", impact=0.9, politics=0.0, credibility=0.9),
            _make_news("Conflict escalation", impact=0.85, politics=0.0, credibility=0.9),
        ]
        for _ in range(5):
            engine.process_day(bad_news)

        final_optimism = engine._calculate_metrics()["average_optimism"]
        assert final_optimism < initial_optimism

    def test_sustained_good_news_maintains_trust(self):
        gen = AgentGenerator()
        agents = gen.generate_agents_for_country("US", 300)
        engine = CountryEngine("US", agents)

        initial_trust = np.mean([a.behavior["trust_institutions"] for a in agents])

        good_news = [_make_news("Economy booming", impact=0.3, politics=0.0, credibility=0.95)]
        for _ in range(10):
            engine.process_day(good_news)

        final_trust = engine._calculate_metrics()["social_cohesion"]
        assert final_trust >= initial_trust - 0.05

    def test_opinion_diffusion_produces_clustering(self):
        """After many days of diffusion, political opinions should cluster."""
        gen = AgentGenerator()
        agents = gen.generate_agents_for_country("US", 200)
        engine = CountryEngine("US", agents)

        initial_pol_std = np.std([a.politics for a in agents])

        # Run 20 days with low-impact news to let diffusion dominate
        mild_news = [_make_news("Minor event", impact=0.1)]
        for _ in range(20):
            engine.process_day(mild_news)

        # After diffusion, opinions should be somewhat more clustered (lower std)
        # or at least not significantly more spread
        final_pol_std = np.std([a.politics for a in agents])
        # Diffusion with bounded confidence should reduce variance
        assert final_pol_std <= initial_pol_std + 0.05
