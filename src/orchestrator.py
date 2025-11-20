import traceback
from typing import Any, Dict, Generator

from .cursor.set_cursor import tint_cursor_color_correct, restore_cursor
from .agent.executor.executor_core import ExecutorCore
from .agent.planner.planner_client import PlannerClient

# Attempt sensible imports with fallbacks depending on package layout
from .agent.planner.planner_client import PlannerClient
from .agent.executor.executor_core import ExecutorCore


REACT_PROMPT = "src/agent/planner/react_prompt.txt"
SUMMARIZER_PROMPT = "src/agent/planner/summarizer_prompt.txt"


def run_orchestrator(prompt: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generator-based orchestrator.

    Yields step dictionaries of the form:
      {"type":"user_prompt", "content": prompt}
      {"type":"thought", "content": <agent_thought_dict>}
      {"type":"tool_result", "content": <executor_result_dict>}
      {"type":"assistant", "content": <final_response_str>}

    This function is intended to be run in a background thread so it does not block the GUI.
    """
    planner = PlannerClient(REACT_PROMPT, SUMMARIZER_PROMPT)
    executor = ExecutorCore()
    tint_cursor_color_correct()

    # 1) announce user prompt
    yield {"type": "user_prompt", "content": prompt}

    try:
        # 2) first planner call with user's input
        parsed = planner.get_next_step(prompt)
        # yield planner thought (full dict so GUI can show "thought" part)
        yield {"type": "thought", "content": parsed}

        # 3) execute loop while planner requests tool_call
        loop_guard = 0
        while isinstance(parsed, dict) and "tool_call" in parsed:
            loop_guard += 1
            if loop_guard > 50:
                # defensive break
                yield {"type": "tool_result", "content": {"status": "error", "error": "too-many-steps"}}
                break

            tool_call = parsed["tool_call"]
            # executor.execute_command should return a dict-like observation
            try:
                result = executor.execute_command(tool_call)
            except Exception as exc:
                # normalize exception to error dict
                result = {"status": "error", "error": str(exc), "traceback": traceback.format_exc()}

            # yield the tool result for UI to render immediately
            yield {"type": "tool_result", "content": result}

            # inform planner about the tool result
            planner.add_tool_response(result)

            # get next step from planner (no user input)
            try:
                parsed = planner.get_next_step()
            except Exception as exc:
                # if planner fails to produce valid JSON / parse error, yield final error as assistant
                yield {"type": "assistant", "content": f"Planner error: {str(exc)}"}
                parsed = None
                break

            # yield planner thought for the new step
            yield {"type": "thought", "content": parsed}

        # 4) when planner returns final_response, yield assistant message
        if isinstance(parsed, dict) and "final_response" in parsed:
            yield {"type": "assistant", "content": parsed.get("final_response")}
        else:
            # if nothing useful, indicate no final response
            yield {"type": "assistant", "content": "(no final_response produced)"}

    except Exception as exc:
        # catch-all for unexpected failures in orchestrator
        yield {"type": "assistant", "content": f"Orchestrator error: {str(exc)}"}
    finally:
        # attempt to summarise history (best-effort)
        try:
            planner.summarize_and_clear_history()
        except Exception:
            pass
        restore_cursor()


if __name__ == "__main__":
    run_orchestrator()