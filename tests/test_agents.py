import numpy as np
import pytest
from collections import Counter
from world_predictor.data.agents import AgentGenerator, COUNTRY_DEMOGRAPHICS, Agent


@pytest.fixture
def generator():
    return AgentGenerator()


class TestAgentGenerator:
    def test_generates_correct_count(self, generator):
        for count in [1, 10, 500]:
            agents = generator.generate_agents_for_country("US", count)
            assert len(agents) == count

    def test_agent_has_all_fields(self, generator):
        agents = generator.generate_agents_for_country("US", 1)
        a = agents[0]
        assert isinstance(a, Agent)
        assert a.id.startswith("US_agent_")
        assert a.location == "US"
        assert isinstance(a.politics, float)
        assert -1.0 <= a.politics <= 1.0
        # Demographics
        for key in ["age", "gender", "race", "religion", "education", "iq"]:
            assert key in a.demographics, f"Missing demographic: {key}"
        # Economic
        for key in ["income", "financial_stability", "career_progression"]:
            assert key in a.economic
        # Behavior
        for key in ["optimism", "risk_aversion", "trust_institutions"]:
            assert key in a.behavior

    def test_all_supported_countries(self, generator):
        for country in ["US", "CN", "IN", "BR", "RU"]:
            agents = generator.generate_agents_for_country(country, 10)
            assert len(agents) == 10
            assert all(a.location == country for a in agents)

    def test_unsupported_country_uses_defaults(self, generator):
        agents = generator.generate_agents_for_country("ZZ", 50)
        assert len(agents) == 50
        assert all(a.location == "ZZ" for a in agents)

    def test_unique_ids(self, generator):
        agents = generator.generate_agents_for_country("US", 100)
        ids = [a.id for a in agents]
        assert len(set(ids)) == 100


class TestDemographicDistributions:
    """Test that distributions roughly match expected proportions (n=5000, tolerance ~3%)."""

    N = 5000
    TOL = 0.04  # 4% tolerance for stochastic tests

    @pytest.fixture(autouse=True)
    def setup(self, generator):
        self.gen = generator

    def _distribution(self, agents, key):
        counts = Counter(a.demographics[key] for a in agents)
        total = len(agents)
        return {k: v / total for k, v in counts.items()}

    def test_us_race_distribution(self):
        agents = self.gen.generate_agents_for_country("US", self.N)
        dist = self._distribution(agents, "race")
        # White should be ~57.8%
        assert abs(dist.get("white", 0) - 0.578) < self.TOL
        # Hispanic ~18.7%
        assert abs(dist.get("hispanic", 0) - 0.187) < self.TOL

    def test_cn_race_distribution(self):
        agents = self.gen.generate_agents_for_country("CN", self.N)
        dist = self._distribution(agents, "race")
        # Han should be ~91.1%
        assert abs(dist.get("han", 0) - 0.911) < self.TOL

    def test_in_religion_distribution(self):
        agents = self.gen.generate_agents_for_country("IN", self.N)
        dist = self._distribution(agents, "religion")
        assert abs(dist.get("hindu", 0) - 0.798) < self.TOL
        assert abs(dist.get("muslim", 0) - 0.142) < self.TOL

    def test_gender_ratio(self):
        agents = self.gen.generate_agents_for_country("RU", self.N)
        dist = self._distribution(agents, "gender")
        # Russia has notable female majority: ~53.7%
        assert abs(dist.get("female", 0) - 0.537) < self.TOL


class TestIQDistribution:
    N = 5000

    def test_iq_mean_per_country(self, generator):
        expected = {"US": 98, "CN": 104, "IN": 82, "BR": 87, "RU": 97}
        for country, expected_mean in expected.items():
            agents = generator.generate_agents_for_country(country, self.N)
            iqs = [int(a.demographics["iq"]) for a in agents]
            actual_mean = np.mean(iqs)
            assert abs(actual_mean - expected_mean) < 3, (
                f"{country}: expected mean ~{expected_mean}, got {actual_mean:.1f}"
            )

    def test_iq_std_roughly_15(self, generator):
        agents = generator.generate_agents_for_country("US", self.N)
        iqs = [int(a.demographics["iq"]) for a in agents]
        assert abs(np.std(iqs) - 15) < 2

    def test_iq_bounds(self, generator):
        agents = generator.generate_agents_for_country("US", 10000)
        iqs = [int(a.demographics["iq"]) for a in agents]
        assert min(iqs) >= 40
        assert max(iqs) <= 200

    def test_iq_education_correlation(self, generator):
        """Higher IQ agents should on average have higher education."""
        agents = generator.generate_agents_for_country("US", self.N)
        edu_order = ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"]
        edu_iq = {}
        for a in agents:
            edu_iq.setdefault(a.demographics["education"], []).append(int(a.demographics["iq"]))

        # Mean IQ of doctorate holders should be higher than no_high_school
        if "doctorate" in edu_iq and "no_high_school" in edu_iq:
            assert np.mean(edu_iq["doctorate"]) > np.mean(edu_iq["no_high_school"])


class TestIncomeDistribution:
    def test_income_positive(self, generator):
        agents = generator.generate_agents_for_country("US", 1000)
        assert all(a.economic["income"] >= 500 for a in agents)

    def test_income_country_differences(self, generator):
        us_agents = generator.generate_agents_for_country("US", 2000)
        in_agents = generator.generate_agents_for_country("IN", 2000)
        us_median = np.median([a.economic["income"] for a in us_agents])
        in_median = np.median([a.economic["income"] for a in in_agents])
        # US median income should be significantly higher than India
        assert us_median > in_median * 3

    def test_financial_stability_correlates_with_income(self, generator):
        agents = generator.generate_agents_for_country("US", 2000)
        high_income = [a for a in agents if a.economic["income"] > 80000]
        low_income = [a for a in agents if a.economic["income"] < 20000]
        if high_income and low_income:
            high_stab = np.mean([a.economic["financial_stability"] for a in high_income])
            low_stab = np.mean([a.economic["financial_stability"] for a in low_income])
            assert high_stab > low_stab


class TestAgeBehaviorCorrelations:
    def test_young_agents_less_advanced_degrees(self, generator):
        agents = generator.generate_agents_for_country("US", 5000)
        young = [a for a in agents if int(a.demographics["age"]) < 25]
        old = [a for a in agents if int(a.demographics["age"]) > 40]
        young_doc = sum(1 for a in young if a.demographics["education"] == "doctorate") / max(len(young), 1)
        old_doc = sum(1 for a in old if a.demographics["education"] == "doctorate") / max(len(old), 1)
        assert young_doc < old_doc

    def test_older_agents_more_risk_averse(self, generator):
        agents = generator.generate_agents_for_country("US", 3000)
        young = [a for a in agents if int(a.demographics["age"]) < 30]
        old = [a for a in agents if int(a.demographics["age"]) > 60]
        if young and old:
            young_risk = np.mean([a.behavior["risk_aversion"] for a in young])
            old_risk = np.mean([a.behavior["risk_aversion"] for a in old])
            assert old_risk > young_risk
