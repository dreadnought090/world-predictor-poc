import random
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Agent:
    id: str
    demographics: Dict[str, str]
    economic: Dict[str, float]
    behavior: Dict[str, float]
    location: str
    politics: float  # -1 to 1

class AgentGenerator:
    def __init__(self):
        self.country_data = self._load_country_data()

    def _load_country_data(self):
        """Load demographic data for countries"""
        return {
            "US": {"population": 331002651, "density": 36},
            "CN": {"population": 1403500365, "density": 153},
            "IN": {"population": 1380004385, "density": 464},
            "BR": {"population": 212559417, "density": 25},
            "RU": {"population": 145934462, "density": 9},
        }

    def generate_agents_for_country(self, country_code: str, count: int = 1000) -> List[Agent]:
        """Generate agents for a specific country"""
        agents = []
        
        for i in range(count):
            agent = Agent(
                id=f"{country_code}agent{i}",
                demographics={
                    "age": str(random.randint(18, 80)),
                    "gender": random.choice(["male", "female", "other"]),
                    "race": self._random_race(country_code),
                    "religion": self._random_religion(country_code),
                    "education": self._random_education()
                },
                economic={
                    "income": self._random_income(country_code),
                    "financial_stability": random.uniform(0, 1),
                    "career_progression": random.uniform(0, 1)
                },
                behavior={
                    "optimism": random.uniform(0, 1),
                    "risk_aversion": random.uniform(0, 1),
                    "trust_institutions": random.uniform(0, 1)
                },
                location=country_code,
                politics=random.uniform(-1, 1)
            )
            agents.append(agent)
        return agents

    def _random_race(self, country_code: str) -> str:
        """Randomly select race based on country demographics"""
        race_distributions = {
            "US": ["white", "black", "hispanic", "asian", "other"],
            "CN": ["han", "zhuang", "uyghur", "other"],
        }
        return random.choice(race_distributions.get(country_code, ["other"]))

    def _random_religion(self, country_code: str) -> str:
        """Randomly select religion based on country demographics"""
        return random.choice(["christian", "muslim", "hindu", "buddhist", "atheist", "other"])

    def _random_education(self) -> str:
        """Randomly select education level"""
        return random.choice(["no high school", "high school", "bachelor", "master", "doctorate"])

    def _random_income(self, country_code: str) -> float:
        """Randomly select income based on country"""
        return random.uniform(1000, 100000)
