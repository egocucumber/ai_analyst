import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

from ai_analyst.app.graph import create_analyst_graph

load_dotenv()

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide"
)

st.title("AI Аналитик Данных")
st.markdown("Загрузите CSV/Excel файл и попросите ИИ построить график или найти инсайты.")

if not os.environ.get("GROQ_API_KEY"):
    st.error("API Key не найден. Проверьте файл .env")
    st.stop()

with st.sidebar:
    st.header("Данные")
    uploaded_file = st.file_uploader("Загрузите файл", type=["csv", "xlsx"])

    if st.button("Сбросить диалог"):
        st.session_state["messages"] = []
        st.rerun()

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.session_state["df"] = df
        st.sidebar.success(f"Файл загружен! Строк: {len(df)}")

        with st.sidebar.expander("Предпросмотр данных"):
            st.dataframe(df.head())

    except Exception as e:
        st.sidebar.error(f"Ошибка чтения файла: {e}")
else:
    st.info("Пожалуйста, загрузите файл в боковой панели, чтобы начать.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Привет! Я вижу ваши данные. Что вы хотите узнать или построить?"}
    ]

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Например: Построй график продаж по датам")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    initial_state = {
        "question": user_input,
        "dataframe": st.session_state["df"],
        "iterations": 0,
        "execution_error": False,
        "figure": None
    }

    app = create_analyst_graph()

    final_state = None

    with st.chat_message("assistant"):
        with st.status("Анализирую данные...", expanded=True) as status:

            for event in app.stream(initial_state):
                for node_name, state_update in event.items():

                    if node_name == "coder":
                        status.write("Coder: Пишу код Python...")
                        with st.expander("Показать код"):
                            st.code(state_update["code"], language="python")

                    elif node_name == "executor":
                        if state_update["execution_error"]:
                            status.write("Executor: Ошибка выполнения!")
                            with st.expander("Ошибка"):
                                st.error(state_update["execution_output"])
                        else:
                            status.write("Executor: Код выполнен успешно.")

                    elif node_name == "debugger":
                        status.write("Debugger: Исправляю код...")

                    final_state = state_update

            status.update(label="Готово!", state="complete", expanded=False)

        if final_state:
            if "figure" in final_state and final_state["figure"]:
                st.plotly_chart(final_state["figure"], use_container_width=True)
                response_content = "Вот график по вашему запросу."

            elif "execution_output" in final_state:
                output_text = final_state["execution_output"]
                st.code(output_text)
                response_content = f"Результат:\n{output_text}"

            else:
                response_content = "Не удалось получить результат."
                st.error("Что-то пошло не так.")

            st.session_state["messages"].append({"role": "assistant", "content": response_content})