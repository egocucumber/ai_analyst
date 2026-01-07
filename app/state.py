from typing import TypedDict, Optional, List, Any
import pandas as pd


class AnalystState(TypedDict):
    question: str
    dataframe: Any

    column_info: str
    code: str

    execution_output: str
    execution_error: bool
    figure: Any

    iterations: int