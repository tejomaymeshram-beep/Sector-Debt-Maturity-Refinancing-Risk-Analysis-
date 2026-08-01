from src.io import load_multiple_csv

from src.config import (
    SECTOR_MASTER_FILE,
    SECTOR_CREDIT_PROFILE_FILE,
    STRESS_PARAMETER_FILE
)

FILES = {

    "sector_master":
        SECTOR_MASTER_FILE,

    "sector_credit":
        SECTOR_CREDIT_PROFILE_FILE,

    "stress":
        STRESS_PARAMETER_FILE

}

data = load_multiple_csv(FILES)

sector_master = data["sector_master"]

sector_credit = data["sector_credit"]

stress = data["stress"]
