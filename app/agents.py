import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq  # <--- Используем Groq
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AnalystState
from .tools import execute_python_code, get_dataframe_info

# Загрузка переменных среды
load_dotenv()

# Проверка ключа
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("❌ ОШИБКА: Не найден GROQ_API_KEY в файле .env")

# Инициализация модели Groq
# llama-3.3-70b-versatile — самая мощная и актуальная на данный момент
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


def clean_code(text: str) -> str:
    """Очищает ответ LLM от маркдауна и лишних слов"""
    # Llama иногда любит поболтать, поэтому чистим жестко
    text = text.strip()

    # Если модель вернула ```python ... ```
    if "```python" in text:
        parts = text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()

    # Если просто ``` ... ```
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("python"):
            text = text[6:]

    return text.strip()


# --- 1. АГЕНТ-ПРОГРАММИСТ ---
def coder_node(state: AnalystState):
    """Генерирует код на основе вопроса и структуры данных"""

    df_info = get_dataframe_info(state['dataframe'])

    prompt = f"""
    Ты опытный Python Data Scientist.
    Твоя задача: Написать код для анализа данных.

    КОНТЕКСТ:
    1. Переменная `df` (pandas DataFrame) уже загружена.
    2. Структура `df`:\n{df_info}
    3. Запрос: "{state['question']}"

    ПРАВИЛА:
    - Используй `pandas`.
    - Если нужен график: используй `plotly.graph_objects` (import as go).
    - ВАЖНО: График должен быть сохранен в переменную `fig`. Не делай fig.show().
    - Если график не нужен: используй `print()` для вывода ответа.
    - НЕ пиши пояснений. Только исполняемый код.
    """

    messages = [
        SystemMessage(content="Ты пишешь только Python код. Никаких объяснений."),
        HumanMessage(content=prompt)
    ]
    response = llm.invoke(messages)

    return {
        "code": clean_code(response.content),
        "iterations": 0,
        "execution_error": False
    }


# --- 2. АГЕНТ-ИСПОЛНИТЕЛЬ (Без изменений) ---
def executor_node(state: AnalystState):
    """Запускает код"""
    result = execute_python_code(state['code'], state['dataframe'])
    return {
        "execution_output": result["output"],
        "execution_error": result["error"],
        "figure": result["figure"]
    }


# --- 3. АГЕНТ-ДЕБАГГЕР ---
def debugger_node(state: AnalystState):
    """Исправляет код"""

    prompt = f"""
    Твой код выдал ошибку. Исправь его.

    НЕПРАВИЛЬНЫЙ КОД:
    {state['code']}

    ОШИБКА:
    {state['execution_output']}

    Верни ТОЛЬКО исправленный Python код без комментариев.
    """

    messages = [
        SystemMessage(content="Ты эксперт по исправлению багов в Python. Пиши только код."),
        HumanMessage(content=prompt)
    ]
    response = llm.invoke(messages)

    return {
        "code": clean_code(response.content),
        "iterations": state['iterations'] + 1
    }