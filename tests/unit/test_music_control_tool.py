import pytest

from providers.tools.music_control_tool import MusicControlTool


def test_music_control_play_track():
    tool = MusicControlTool()
    params = {"action": "play", "track": "I'm Alive - Celine Dion"}
    assert tool.validate_parameters(params) is True
    result = tool.execute(params)
    assert result.success is True
    assert result.data["action"] == "play"


def test_music_control_pause():
    tool = MusicControlTool()
    params = {"action": "pause"}
    assert tool.validate_parameters(params) is True
    result = tool.execute(params)
    assert result.success is True
    assert result.data["action"] == "pause"


def test_music_control_set_volume_valid():
    tool = MusicControlTool()
    params = {"action": "set_volume", "level": 30}
    assert tool.validate_parameters(params) is True
    result = tool.execute(params)
    assert result.success is True
    assert result.data["level"] == 30


def test_music_control_set_volume_invalid():
    tool = MusicControlTool()
    params = {"action": "set_volume", "level": 200}
    assert tool.validate_parameters(params) is False

