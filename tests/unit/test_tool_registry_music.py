from services.tool_registry import ToolRegistry
from providers.tools.music_control_tool import MusicControlTool


def test_register_and_execute_music_tool_named():
    registry = ToolRegistry()
    tool = MusicControlTool()
    assert registry.register_tool("music_control", tool) is True
    assert "music_control" in registry.get_available_tools()

    # Execute pause
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        registry.execute_tool("music_control", {"action": "pause"})
    )
    assert result.success is True
    assert result.data["action"] == "pause"


def test_register_and_execute_music_tool_infer_name():
    registry = ToolRegistry()
    tool = MusicControlTool()
    assert registry.register_tool(tool) is True
    assert "music_control" in registry.get_available_tools()

    # Execute set_volume
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        registry.execute_tool("music_control", {"action": "set_volume", "level": 25})
    )
    assert result.success is True
    assert result.data["level"] == 25

