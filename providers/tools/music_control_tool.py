"""
Music Control Tool
Single-responsibility tool that exposes media control actions behind a simple
parameterized interface. Follows SOLID: interface-driven design, easy to extend
with new providers (system, Spotify, etc.) without modifying callers.
"""

from typing import Dict, Any, List, Optional

from core.interfaces.tool_provider import (
    IToolProvider,
    ToolCategory,
    ToolAuthType,
    ToolParameter,
    ToolResult,
)


class IMediaController:
    """Abstraction for media control backends (Open/Closed for extension)."""

    def play(self, track: Optional[str] = None, playlist: Optional[str] = None) -> ToolResult:
        raise NotImplementedError

    def pause(self) -> ToolResult:
        raise NotImplementedError

    def resume(self) -> ToolResult:
        raise NotImplementedError

    def next(self) -> ToolResult:
        raise NotImplementedError

    def previous(self) -> ToolResult:
        raise NotImplementedError

    def set_volume(self, level: int) -> ToolResult:
        raise NotImplementedError


class SystemMediaController(IMediaController):
    """Minimal stub system controller.
    Replace implementations per-OS (e.g., pycaw, playerctl, AppleScript) later.
    """

    def play(self, track: Optional[str] = None, playlist: Optional[str] = None) -> ToolResult:
        details = {"track": track, "playlist": playlist}
        return ToolResult(success=True, data={"action": "play", **{k: v for k, v in details.items() if v}})

    def pause(self) -> ToolResult:
        return ToolResult(success=True, data={"action": "pause"})

    def resume(self) -> ToolResult:
        return ToolResult(success=True, data={"action": "resume"})

    def next(self) -> ToolResult:
        return ToolResult(success=True, data={"action": "next"})

    def previous(self) -> ToolResult:
        return ToolResult(success=True, data={"action": "previous"})

    def set_volume(self, level: int) -> ToolResult:
        return ToolResult(success=True, data={"action": "set_volume", "level": level})


class MusicControlTool(IToolProvider):
    """Music control tool implementing IToolProvider.
    Delegates actual control to a pluggable IMediaController implementation.
    """

    def __init__(self, controller: Optional[IMediaController] = None) -> None:
        self.controller = controller or SystemMediaController()

    # IToolProvider metadata
    def get_tool_name(self) -> str:
        return "music_control"

    def get_tool_description(self) -> str:
        return "Control music playback: play, pause, resume, next, previous, set volume"

    def get_tool_category(self) -> ToolCategory:
        return ToolCategory.SYSTEM

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True,
                options=["play", "pause", "resume", "next", "previous", "set_volume"],
            ),
            ToolParameter(
                name="track",
                type="string",
                description="Track name (for play)",
                required=False,
            ),
            ToolParameter(
                name="playlist",
                type="string",
                description="Playlist name (for play)",
                required=False,
            ),
            ToolParameter(
                name="level",
                type="number",
                description="Volume level 0-100 (for set_volume)",
                required=False,
                default=50,
            ),
            ToolParameter(
                name="provider",
                type="string",
                description="Backend provider (system, spotify)",
                required=False,
                default="system",
                options=["system", "spotify"],
            ),
        ]

    def get_auth_type(self) -> ToolAuthType:
        return ToolAuthType.NONE

    def is_available(self) -> bool:
        return True

    # Validation and execution
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if "action" not in parameters:
            return False
        action = parameters.get("action")
        if action not in {"play", "pause", "resume", "next", "previous", "set_volume"}:
            return False
        if action == "set_volume":
            level = parameters.get("level")
            if level is None or not isinstance(level, (int, float)) or not (0 <= int(level) <= 100):
                return False
        return True

    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        action = parameters.get("action")
        track = parameters.get("track")
        playlist = parameters.get("playlist")
        level = parameters.get("level")

        try:
            if action == "play":
                return self.controller.play(track=track, playlist=playlist)
            if action == "pause":
                return self.controller.pause()
            if action == "resume":
                return self.controller.resume()
            if action == "next":
                return self.controller.next()
            if action == "previous":
                return self.controller.previous()
            if action == "set_volume":
                return self.controller.set_volume(int(level))
            return ToolResult(success=False, error=f"Unsupported action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

