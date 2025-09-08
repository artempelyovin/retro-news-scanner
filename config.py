import os
from dataclasses import dataclass


@dataclass
class Config:
    database_file: str


config = Config(
    database_file=os.getenv("DATABASE_FILE", "lenta.db"),
)
