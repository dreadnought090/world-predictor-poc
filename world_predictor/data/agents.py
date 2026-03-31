import random
from typing import Dict, List
from dataclasses import dataclass
import numpy as np

@dataclass
class Agent:
    id: str
    demographics: Dict[str, str]
    economic: Dict[str, float]
    behavior: Dict[str, float]
    location: str
    politics: float  # -1 to 1

# ---------------------------------------------------------------------------
# Real-world demographic distributions per country
# Sources: US Census Bureau, Pew Research, World Bank, OECD, national census
# ---------------------------------------------------------------------------

COUNTRY_DEMOGRAPHICS = {
    "US": {
        "population": 331_002_651,
        "density": 36,
        "race": {
            "labels": ["white", "hispanic", "black", "asian", "multiracial", "native_american", "pacific_islander"],
            "weights": [57.8, 18.7, 12.4, 5.9, 3.7, 0.9, 0.6],
        },
        "religion": {
            "labels": ["christian", "unaffiliated", "jewish", "muslim", "buddhist", "hindu", "other"],
            "weights": [65.0, 26.0, 2.0, 1.1, 1.0, 0.7, 4.2],
        },
        "education": {
            "labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"],
            "weights": [11.0, 27.0, 20.0, 22.0, 13.0, 7.0],
        },
        "age_brackets": {
            "ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)],
            "weights": [12.0, 18.0, 16.5, 16.0, 17.0, 20.5],
        },
        "gender": {
            "labels": ["male", "female"],
            "weights": [49.5, 50.5],
        },
        "income": {
            "median_usd": 37_500,
            "sigma": 0.85,
        },
        "iq": {"mean": 98, "std": 15},
        "politics_mean": 0.0,
        "politics_std": 0.45,
    },
    "CN": {
        "population": 1_403_500_365,
        "density": 153,
        "race": {
            "labels": ["han", "zhuang", "hui", "manchu", "uyghur", "miao", "other_minority"],
            "weights": [91.1, 1.3, 0.8, 0.8, 0.8, 0.7, 4.5],
        },
        "religion": {
            "labels": ["folk_religion", "buddhist", "unaffiliated", "christian", "muslim", "other"],
            "weights": [21.9, 18.2, 52.0, 5.1, 1.8, 1.0],
        },
        "education": {
            "labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"],
            "weights": [30.0, 28.0, 18.0, 17.0, 5.5, 1.5],
        },
        "age_brackets": {
            "ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)],
            "weights": [9.0, 15.0, 16.0, 18.0, 18.0, 24.0],
        },
        "gender": {
            "labels": ["male", "female"],
            "weights": [51.2, 48.8],
        },
        "income": {
            "median_usd": 12_000,
            "sigma": 0.90,
        },
        "iq": {"mean": 104, "std": 14},
        "politics_mean": 0.3,
        "politics_std": 0.25,
    },
    "IN": {
        "population": 1_380_004_385,
        "density": 464,
        "race": {
            "labels": ["indo_aryan", "dravidian", "mongoloid", "other"],
            "weights": [72.0, 25.0, 2.0, 1.0],
        },
        "religion": {
            "labels": ["hindu", "muslim", "christian", "sikh", "buddhist", "jain", "other"],
            "weights": [79.8, 14.2, 2.3, 1.7, 0.7, 0.4, 0.9],
        },
        "education": {
            "labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"],
            "weights": [44.0, 24.0, 14.0, 12.0, 4.5, 1.5],
        },
        "age_brackets": {
            "ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)],
            "weights": [20.0, 22.0, 18.0, 15.0, 13.0, 12.0],
        },
        "gender": {
            "labels": ["male", "female"],
            "weights": [51.6, 48.4],
        },
        "income": {
            "median_usd": 3_500,
            "sigma": 1.0,
        },
        "iq": {"mean": 82, "std": 15},
        "politics_mean": 0.1,
        "politics_std": 0.50,
    },
    "BR": {
        "population": 212_559_417,
        "density": 25,
        "race": {
            "labels": ["white", "pardo", "black", "asian", "indigenous"],
            "weights": [43.0, 46.5, 8.9, 1.1, 0.5],
        },
        "religion": {
            "labels": ["catholic", "protestant", "unaffiliated", "spiritist", "other"],
            "weights": [50.0, 31.0, 10.0, 3.0, 6.0],
        },
        "education": {
            "labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"],
            "weights": [33.0, 32.0, 15.0, 14.0, 4.5, 1.5],
        },
        "age_brackets": {
            "ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)],
            "weights": [16.0, 20.0, 18.0, 16.0, 15.0, 15.0],
        },
        "gender": {
            "labels": ["male", "female"],
            "weights": [49.3, 50.7],
        },
        "income": {
            "median_usd": 8_500,
            "sigma": 0.95,
        },
        "iq": {"mean": 87, "std": 15},
        "politics_mean": 0.05,
        "politics_std": 0.55,
    },
    "RU": {
        "population": 145_934_462,
        "density": 9,
        "race": {
            "labels": ["russian", "tatar", "bashkir", "chechen", "chuvash", "other_minority"],
            "weights": [77.7, 3.7, 1.2, 1.1, 1.0, 15.3],
        },
        "religion": {
            "labels": ["orthodox_christian", "unaffiliated", "muslim", "other_christian", "buddhist", "other"],
            "weights": [47.0, 25.0, 15.0, 6.0, 1.5, 5.5],
        },
        "education": {
            "labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"],
            "weights": [6.0, 28.0, 25.0, 27.0, 10.0, 4.0],
        },
        "age_brackets": {
            "ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)],
            "weights": [10.0, 16.0, 17.0, 15.0, 18.0, 24.0],
        },
        "gender": {
            "labels": ["male", "female"],
            "weights": [46.3, 53.7],
        },
        "income": {
            "median_usd": 10_000,
            "sigma": 0.80,
        },
        "iq": {"mean": 97, "std": 15},
        "politics_mean": 0.25,
        "politics_std": 0.30,
    },

    # --- Expanded countries ---

    "JP": {
        "population": 125_800_000, "density": 347,
        "race": {"labels": ["japanese", "korean", "chinese", "other"], "weights": [97.5, 0.9, 0.6, 1.0]},
        "religion": {"labels": ["shinto_buddhist", "unaffiliated", "christian", "other"], "weights": [69.0, 26.0, 2.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [5.0, 25.0, 22.0, 32.0, 11.0, 5.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [8.0, 12.0, 14.0, 15.0, 17.0, 34.0]},
        "gender": {"labels": ["male", "female"], "weights": [48.8, 51.2]},
        "income": {"median_usd": 30_000, "sigma": 0.70},
        "iq": {"mean": 106, "std": 14},
        "politics_mean": 0.15, "politics_std": 0.30,
    },
    "DE": {
        "population": 83_200_000, "density": 240,
        "race": {"labels": ["german", "turkish", "polish", "syrian", "other"], "weights": [75.0, 3.5, 2.5, 1.5, 17.5]},
        "religion": {"labels": ["christian", "unaffiliated", "muslim", "other"], "weights": [52.0, 37.0, 7.0, 4.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [8.0, 30.0, 22.0, 22.0, 13.0, 5.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [9.0, 14.0, 14.0, 16.0, 17.0, 30.0]},
        "gender": {"labels": ["male", "female"], "weights": [49.3, 50.7]},
        "income": {"median_usd": 35_000, "sigma": 0.75},
        "iq": {"mean": 100, "std": 15},
        "politics_mean": -0.05, "politics_std": 0.40,
    },
    "GB": {
        "population": 67_800_000, "density": 281,
        "race": {"labels": ["white_british", "asian", "black", "mixed", "other"], "weights": [80.5, 9.3, 4.0, 2.9, 3.3]},
        "religion": {"labels": ["christian", "unaffiliated", "muslim", "hindu", "other"], "weights": [46.0, 37.0, 7.0, 2.0, 8.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [10.0, 25.0, 18.0, 27.0, 14.0, 6.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [10.0, 16.0, 15.0, 16.0, 16.0, 27.0]},
        "gender": {"labels": ["male", "female"], "weights": [49.4, 50.6]},
        "income": {"median_usd": 33_000, "sigma": 0.80},
        "iq": {"mean": 100, "std": 15},
        "politics_mean": 0.0, "politics_std": 0.45,
    },
    "FR": {
        "population": 67_400_000, "density": 119,
        "race": {"labels": ["french", "north_african", "sub_saharan", "european_other", "other"], "weights": [72.0, 10.0, 5.0, 8.0, 5.0]},
        "religion": {"labels": ["christian", "unaffiliated", "muslim", "jewish", "other"], "weights": [47.0, 40.0, 9.0, 1.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [12.0, 28.0, 18.0, 22.0, 14.0, 6.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [10.0, 14.0, 15.0, 16.0, 16.0, 29.0]},
        "gender": {"labels": ["male", "female"], "weights": [48.7, 51.3]},
        "income": {"median_usd": 31_000, "sigma": 0.78},
        "iq": {"mean": 98, "std": 15},
        "politics_mean": -0.05, "politics_std": 0.50,
    },
    "KR": {
        "population": 51_800_000, "density": 527,
        "race": {"labels": ["korean", "chinese", "other"], "weights": [96.0, 2.0, 2.0]},
        "religion": {"labels": ["unaffiliated", "protestant", "buddhist", "catholic", "other"], "weights": [56.0, 20.0, 16.0, 6.0, 2.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [5.0, 22.0, 20.0, 34.0, 13.0, 6.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [9.0, 14.0, 15.0, 17.0, 17.0, 28.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.0, 50.0]},
        "income": {"median_usd": 28_000, "sigma": 0.75},
        "iq": {"mean": 106, "std": 14},
        "politics_mean": 0.05, "politics_std": 0.45,
    },
    "AU": {
        "population": 26_000_000, "density": 3,
        "race": {"labels": ["european", "asian", "indigenous", "other"], "weights": [70.0, 17.0, 3.5, 9.5]},
        "religion": {"labels": ["christian", "unaffiliated", "muslim", "buddhist", "hindu", "other"], "weights": [44.0, 39.0, 3.0, 3.0, 3.0, 8.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [9.0, 25.0, 20.0, 26.0, 14.0, 6.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [11.0, 17.0, 16.0, 16.0, 15.0, 25.0]},
        "gender": {"labels": ["male", "female"], "weights": [49.7, 50.3]},
        "income": {"median_usd": 36_000, "sigma": 0.80},
        "iq": {"mean": 99, "std": 15},
        "politics_mean": 0.0, "politics_std": 0.40,
    },
    "MX": {
        "population": 128_900_000, "density": 66,
        "race": {"labels": ["mestizo", "indigenous", "white", "afro_mexican", "other"], "weights": [62.0, 21.0, 12.0, 1.5, 3.5]},
        "religion": {"labels": ["catholic", "protestant", "unaffiliated", "other"], "weights": [78.0, 11.0, 8.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [35.0, 30.0, 15.0, 14.0, 4.0, 2.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [16.0, 20.0, 18.0, 16.0, 14.0, 16.0]},
        "gender": {"labels": ["male", "female"], "weights": [49.3, 50.7]},
        "income": {"median_usd": 7_000, "sigma": 0.95},
        "iq": {"mean": 88, "std": 15},
        "politics_mean": 0.0, "politics_std": 0.50,
    },
    "ID": {
        "population": 273_500_000, "density": 151,
        "race": {"labels": ["javanese", "sundanese", "malay", "batak", "other"], "weights": [40.0, 15.5, 4.0, 3.5, 37.0]},
        "religion": {"labels": ["muslim", "protestant", "catholic", "hindu", "buddhist", "other"], "weights": [87.0, 7.0, 3.0, 1.7, 0.7, 0.6]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [40.0, 28.0, 14.0, 12.0, 4.0, 2.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [17.0, 21.0, 19.0, 16.0, 14.0, 13.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.1, 49.9]},
        "income": {"median_usd": 4_500, "sigma": 0.90},
        "iq": {"mean": 87, "std": 15},
        "politics_mean": 0.1, "politics_std": 0.40,
    },
    "NG": {
        "population": 223_800_000, "density": 226,
        "race": {"labels": ["hausa_fulani", "yoruba", "igbo", "other"], "weights": [30.0, 21.0, 18.0, 31.0]},
        "religion": {"labels": ["muslim", "christian", "traditional", "other"], "weights": [50.0, 40.0, 7.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [50.0, 25.0, 12.0, 9.0, 3.0, 1.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [25.0, 24.0, 19.0, 14.0, 10.0, 8.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.5, 49.5]},
        "income": {"median_usd": 2_000, "sigma": 1.1},
        "iq": {"mean": 77, "std": 15},
        "politics_mean": 0.0, "politics_std": 0.55,
    },
    "EG": {
        "population": 104_000_000, "density": 103,
        "race": {"labels": ["arab_egyptian", "nubian", "berber", "other"], "weights": [91.0, 4.0, 2.0, 3.0]},
        "religion": {"labels": ["muslim", "christian", "other"], "weights": [90.0, 9.0, 1.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [35.0, 30.0, 15.0, 14.0, 4.0, 2.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [18.0, 22.0, 19.0, 16.0, 13.0, 12.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.8, 49.2]},
        "income": {"median_usd": 4_000, "sigma": 0.95},
        "iq": {"mean": 83, "std": 15},
        "politics_mean": 0.3, "politics_std": 0.30,
    },
    "SA": {
        "population": 36_000_000, "density": 16,
        "race": {"labels": ["arab", "south_asian", "southeast_asian", "african", "other"], "weights": [62.0, 20.0, 10.0, 5.0, 3.0]},
        "religion": {"labels": ["sunni_muslim", "shia_muslim", "other"], "weights": [85.0, 12.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [20.0, 30.0, 20.0, 20.0, 7.0, 3.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [16.0, 22.0, 20.0, 18.0, 14.0, 10.0]},
        "gender": {"labels": ["male", "female"], "weights": [58.0, 42.0]},
        "income": {"median_usd": 22_000, "sigma": 0.85},
        "iq": {"mean": 84, "std": 15},
        "politics_mean": 0.4, "politics_std": 0.20,
    },
    "TR": {
        "population": 85_300_000, "density": 110,
        "race": {"labels": ["turkish", "kurdish", "arab", "other"], "weights": [75.0, 18.0, 4.0, 3.0]},
        "religion": {"labels": ["sunni_muslim", "alevi", "unaffiliated", "other"], "weights": [75.0, 15.0, 7.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [25.0, 30.0, 18.0, 18.0, 6.0, 3.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [14.0, 19.0, 18.0, 16.0, 15.0, 18.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.2, 49.8]},
        "income": {"median_usd": 10_500, "sigma": 0.85},
        "iq": {"mean": 90, "std": 15},
        "politics_mean": 0.2, "politics_std": 0.50,
    },
    "PK": {
        "population": 231_400_000, "density": 287,
        "race": {"labels": ["punjabi", "pashtun", "sindhi", "muhajir", "baloch", "other"], "weights": [44.0, 15.0, 14.0, 8.0, 4.0, 15.0]},
        "religion": {"labels": ["sunni_muslim", "shia_muslim", "ahmadi", "christian", "hindu", "other"], "weights": [80.0, 15.0, 1.5, 1.5, 1.0, 1.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [50.0, 22.0, 12.0, 10.0, 4.0, 2.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [22.0, 23.0, 19.0, 15.0, 12.0, 9.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.8, 49.2]},
        "income": {"median_usd": 2_800, "sigma": 1.0},
        "iq": {"mean": 80, "std": 15},
        "politics_mean": 0.15, "politics_std": 0.50,
    },
    "PH": {
        "population": 115_600_000, "density": 368,
        "race": {"labels": ["tagalog", "visayan", "ilocano", "other"], "weights": [28.0, 30.0, 9.0, 33.0]},
        "religion": {"labels": ["catholic", "protestant", "muslim", "iglesia_ni_cristo", "other"], "weights": [79.0, 9.0, 6.0, 3.0, 3.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [25.0, 30.0, 20.0, 18.0, 5.0, 2.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [19.0, 21.0, 18.0, 16.0, 14.0, 12.0]},
        "gender": {"labels": ["male", "female"], "weights": [50.0, 50.0]},
        "income": {"median_usd": 3_500, "sigma": 0.95},
        "iq": {"mean": 86, "std": 15},
        "politics_mean": 0.05, "politics_std": 0.45,
    },
    "TH": {
        "population": 71_800_000, "density": 137,
        "race": {"labels": ["thai", "chinese_thai", "malay", "other"], "weights": [75.0, 14.0, 4.0, 7.0]},
        "religion": {"labels": ["buddhist", "muslim", "christian", "other"], "weights": [93.0, 5.0, 1.0, 1.0]},
        "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [30.0, 28.0, 18.0, 16.0, 5.0, 3.0]},
        "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [11.0, 16.0, 17.0, 17.0, 17.0, 22.0]},
        "gender": {"labels": ["male", "female"], "weights": [49.0, 51.0]},
        "income": {"median_usd": 7_500, "sigma": 0.85},
        "iq": {"mean": 91, "std": 15},
        "politics_mean": 0.15, "politics_std": 0.40,
    },
}

# Fallback for unsupported countries
_DEFAULT_DEMOGRAPHICS = {
    "race": {"labels": ["majority", "minority_a", "minority_b", "other"], "weights": [60, 20, 15, 5]},
    "religion": {"labels": ["religion_a", "religion_b", "unaffiliated", "other"], "weights": [40, 30, 20, 10]},
    "education": {"labels": ["no_high_school", "high_school", "some_college", "bachelor", "master", "doctorate"], "weights": [20, 30, 20, 18, 8, 4]},
    "age_brackets": {"ranges": [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 80)], "weights": [15, 18, 17, 16, 16, 18]},
    "gender": {"labels": ["male", "female"], "weights": [50, 50]},
    "income": {"median_usd": 10_000, "sigma": 0.90},
    "iq": {"mean": 90, "std": 15},
    "politics_mean": 0.0,
    "politics_std": 0.40,
}


class AgentGenerator:
    def __init__(self):
        self.country_data = COUNTRY_DEMOGRAPHICS

    def _get_demo(self, country_code: str) -> dict:
        """Get demographic data for a country, falling back to defaults."""
        if country_code in self.country_data:
            return self.country_data[country_code]
        # Merge defaults with basic population info
        return {**_DEFAULT_DEMOGRAPHICS, "population": 0, "density": 0}

    def generate_agents_for_country(self, country_code: str, count: int = 1000) -> List[Agent]:
        """Generate agents with realistic demographic distributions."""
        demo = self._get_demo(country_code)
        agents = []

        # Pre-generate income array for efficiency (log-normal distribution)
        income_params = demo.get("income", _DEFAULT_DEMOGRAPHICS["income"])
        log_median = np.log(income_params["median_usd"])
        incomes = np.random.lognormal(mean=log_median, sigma=income_params["sigma"], size=count)
        incomes = np.clip(incomes, 500, 1_000_000)  # reasonable bounds

        # Pre-generate politics array (truncated normal)
        pol_mean = demo.get("politics_mean", 0.0)
        pol_std = demo.get("politics_std", 0.4)
        politics_arr = np.random.normal(pol_mean, pol_std, size=count)
        politics_arr = np.clip(politics_arr, -1.0, 1.0)

        # Pre-generate IQ array (normal distribution, country-specific mean)
        iq_params = demo.get("iq", _DEFAULT_DEMOGRAPHICS["iq"])
        iq_arr = np.random.normal(iq_params["mean"], iq_params["std"], size=count)
        iq_arr = np.clip(iq_arr, 40, 200).astype(int)

        for i in range(count):
            age = self._weighted_age(demo)
            iq = int(iq_arr[i])
            education = self._weighted_education(demo, age, iq)
            agent = Agent(
                id=f"{country_code}_agent_{i}",
                demographics={
                    "age": str(age),
                    "gender": self._weighted_pick(demo, "gender"),
                    "race": self._weighted_pick(demo, "race"),
                    "religion": self._weighted_pick(demo, "religion"),
                    "education": education,
                    "iq": str(iq),
                },
                economic={
                    "income": round(float(incomes[i]), 2),
                    "financial_stability": self._income_to_stability(float(incomes[i]), income_params["median_usd"]),
                    "career_progression": self._age_to_career(age),
                },
                behavior={
                    "optimism": random.uniform(0.2, 0.9),
                    "risk_aversion": self._age_to_risk_aversion(age),
                    "trust_institutions": random.uniform(0.15, 0.85),
                },
                location=country_code,
                politics=round(float(politics_arr[i]), 4),
            )
            agents.append(agent)
        return agents

    # --- Weighted selection helpers ---

    def _weighted_pick(self, demo: dict, category: str) -> str:
        """Pick a value from a weighted distribution."""
        data = demo.get(category, _DEFAULT_DEMOGRAPHICS.get(category))
        return random.choices(data["labels"], weights=data["weights"], k=1)[0]

    def _weighted_age(self, demo: dict) -> int:
        """Pick an age from weighted age brackets, then uniform within bracket."""
        brackets = demo.get("age_brackets", _DEFAULT_DEMOGRAPHICS["age_brackets"])
        chosen_range = random.choices(brackets["ranges"], weights=brackets["weights"], k=1)[0]
        return random.randint(chosen_range[0], chosen_range[1])

    def _weighted_education(self, demo: dict, age: int, iq: int = 100) -> str:
        """Pick education, skewed by age and correlated with IQ.

        Higher IQ increases probability of higher education levels;
        lower IQ shifts weight toward lower education levels.
        """
        data = demo.get("education", _DEFAULT_DEMOGRAPHICS["education"])
        labels = data["labels"]
        # labels: [no_high_school, high_school, some_college, bachelor, master, doctorate]
        weights = list(data["weights"])

        # IQ correlation: shift weights toward higher/lower education
        # Neutral at IQ=100; each 15 points = ~1 std deviation
        iq_factor = (iq - 100) / 15.0  # z-score relative to global mean

        if iq_factor > 0:
            # Higher IQ: boost upper education, reduce lower
            weights[0] *= max(0.1, 1 - iq_factor * 0.3)   # no_high_school
            weights[1] *= max(0.2, 1 - iq_factor * 0.2)   # high_school
            weights[3] *= 1 + iq_factor * 0.4              # bachelor
            weights[4] *= 1 + iq_factor * 0.6              # master
            weights[5] *= 1 + iq_factor * 0.8              # doctorate
        else:
            # Lower IQ: boost lower education, reduce upper
            abs_factor = abs(iq_factor)
            weights[0] *= 1 + abs_factor * 0.5             # no_high_school
            weights[1] *= 1 + abs_factor * 0.3             # high_school
            weights[3] *= max(0.1, 1 - abs_factor * 0.3)   # bachelor
            weights[4] *= max(0.05, 1 - abs_factor * 0.5)  # master
            weights[5] *= max(0.02, 1 - abs_factor * 0.7)  # doctorate

        # Age constraints: young people haven't had time for advanced degrees
        if age < 25:
            weights[4] *= 0.1   # master
            weights[5] *= 0.02  # doctorate
            weights[3] *= 0.5   # bachelor less likely
        elif age < 30:
            weights[5] *= 0.2   # doctorate still rare
            weights[4] *= 0.5   # master less common

        return random.choices(labels, weights=weights, k=1)[0]

    # --- Derived attribute helpers ---

    def _income_to_stability(self, income: float, median: float) -> float:
        """Higher income relative to median = more financial stability."""
        ratio = income / max(median, 1)
        # Sigmoid-like mapping: ratio 1.0 -> ~0.5 stability
        stability = ratio / (ratio + 1.0)
        return round(min(1.0, max(0.0, stability)), 4)

    def _age_to_career(self, age: int) -> float:
        """Career progression peaks around 45-55."""
        if age < 25:
            return random.uniform(0.05, 0.25)
        elif age < 35:
            return random.uniform(0.2, 0.55)
        elif age < 50:
            return random.uniform(0.4, 0.85)
        elif age < 60:
            return random.uniform(0.5, 0.9)
        else:
            return random.uniform(0.3, 0.7)

    def _age_to_risk_aversion(self, age: int) -> float:
        """Older people tend to be more risk-averse."""
        base = 0.2 + (age - 18) / (80 - 18) * 0.5
        return round(min(1.0, max(0.0, base + random.uniform(-0.15, 0.15))), 4)
