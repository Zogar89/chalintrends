from chalintrends.live_search import LIVE_SEARCH_JS


def test_live_search_emits_value_on_each_keystroke():
    assert "input.oninput" in LIVE_SEARCH_JS
    assert 'setStateValue("value"' in LIVE_SEARCH_JS
