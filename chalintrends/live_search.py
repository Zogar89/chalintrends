from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

LIVE_SEARCH_HTML = """
<div class="live-search">
  <input id="live-search-input" type="search" autocomplete="off" spellcheck="false" />
</div>
"""

LIVE_SEARCH_CSS = """
.live-search {
  width: 100%;
}

#live-search-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 52px;
  border: 1px solid var(--st-border-color, #e0d5c5);
  border-radius: 8px;
  background: var(--st-background-color, #ffffff);
  color: var(--st-text-color, #172033);
  font: inherit;
  font-size: 18px;
  padding: 0 14px;
  outline: none;
}

#live-search-input:focus {
  border-color: var(--st-primary-color, #a82d25);
  box-shadow: 0 0 0 2px rgba(168, 45, 37, .12);
}

#live-search-input::placeholder {
  color: var(--st-text-color, #687180);
  opacity: .68;
}
"""

LIVE_SEARCH_JS = """
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const input = parentElement.querySelector("#live-search-input")
  if (!input) return

  input.placeholder = (data && data.placeholder) || ""
  input.setAttribute("aria-label", (data && data.label) || "Buscar")

  const nextValue = (data && data.value) || ""
  if (input.value !== nextValue) {
    input.value = nextValue
  }

  input.oninput = (event) => {
    setStateValue("value", event.target.value)
  }

  return () => {
    input.oninput = null
  }
}
"""

_LIVE_SEARCH_COMPONENT = st.components.v2.component(
    "chalintrends_live_search",
    html=LIVE_SEARCH_HTML,
    css=LIVE_SEARCH_CSS,
    js=LIVE_SEARCH_JS,
)


def _read_state_value(state: Any, fallback: str) -> str:
    if isinstance(state, dict):
        return str(state.get("value") or fallback)
    return str(getattr(state, "value", fallback) or fallback)


def live_search_input(
    label: str,
    *,
    placeholder: str = "",
    key: str = "live_search",
    value: str = "",
    on_value_change: Callable[[], None] | None = None,
) -> str:
    current_value = _read_state_value(st.session_state.get(key), value)
    result = _LIVE_SEARCH_COMPONENT(
        data={"label": label, "placeholder": placeholder, "value": current_value},
        key=key,
        on_value_change=on_value_change or (lambda: None),
    )
    return _read_state_value(result, current_value)
