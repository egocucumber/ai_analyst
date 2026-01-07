import sys
import io
import pandas as pd
import plotly.graph_objects as go


def get_dataframe_info(df: pd.DataFrame) -> str:
    """Генерирует описание датафрейма для LLM"""
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    head_str = df.head(3).to_markdown(index=False, numalign="left", stralign="left")

    return f"INFO:\n{info_str}\n\nHEAD (Samples):\n{head_str}"


def execute_python_code(code: str, df: pd.DataFrame):
    """
    Выполняет Python код.
    Ожидает, что код использует переменную `df`.
    Если нужен график, код должен сохранить его в переменную `fig`.
    """
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()

    local_scope = {
        "df": df,
        "pd": pd,
        "go": go,
        "fig": None
    }

    try:
        exec(code, {}, local_scope)

        captured_output = redirected_output.getvalue()
        figure = local_scope.get("fig")

        return {
            "output": captured_output,
            "error": False,
            "figure": figure
        }

    except Exception as e:
        import traceback
        return {
            "output": traceback.format_exc(),
            "error": True,
            "figure": None
        }
    finally:
        sys.stdout = old_stdout