"""Any jobs that does data processing, such as:
- cleaning
- transformation
- feature selection
- e.t.c
"""
from .job import GetTrainingData
from .job import DropNullAndDuplicateRow
from .job import DropNullColumns
from .job import SetTrainingData


__all__ = [
    "GetTrainingData",
    "DropNullAndDuplicateRow",
    "DropNullColumns",
    "SetTrainingData"
]
