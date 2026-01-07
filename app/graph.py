from langgraph.graph import StateGraph, END
from .state import AnalystState
from .agents import coder_node, executor_node, debugger_node


def should_continue(state: AnalystState):
    """Решает, куда идти после выполнения кода"""

    if not state['execution_error']:
        return "end"

    if state['iterations'] >= 3:
        return "end"

    return "debug"


def create_analyst_graph():
    workflow = StateGraph(AnalystState)

    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("debugger", debugger_node)

    workflow.set_entry_point("coder")

    workflow.add_edge("coder", "executor")
    workflow.add_edge("debugger", "executor")

    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {
            "end": END,
            "debug": "debugger"
        }
    )

    return workflow.compile()