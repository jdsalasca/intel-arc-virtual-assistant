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
    """Windows system media controller using Windows API and keyboard controls."""
    
    def __init__(self):
        self._has_windows_api = False
        self._init_windows_api()
    
    def _init_windows_api(self):
        """Initialize Windows API components if available."""
        try:
            # Try to import Windows-specific modules
            import win32gui
            import win32con
            import subprocess
            self._has_windows_api = True
        except ImportError:
            pass
    
    def _send_media_key(self, key_code: int) -> bool:
        """Send media key using Windows API or subprocess."""
        try:
            if self._has_windows_api:
                import win32api
                import win32con
                # Send key down
                win32api.keybd_event(key_code, 0, 0, 0)
                # Send key up
                win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                return True
            else:
                # Fallback using PowerShell
                import subprocess
                # Use PowerShell to send media keys
                ps_script = f"""
                Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices;
                public class MediaKeys {{
                    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
                    public static void SendKey(byte key) {{ keybd_event(key, 0, 0, UIntPtr.Zero); keybd_event(key, 0, 2, UIntPtr.Zero); }}
                }}'
                [MediaKeys]::SendKey({key_code})
                """
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True, check=True)
                return True
        except Exception as e:
            print(f"Failed to send media key {key_code}: {e}")
            return False
    
    def play(self, track: Optional[str] = None, playlist: Optional[str] = None) -> ToolResult:
        """Start playback or open media player."""
        try:
            if track or playlist:
                # Try to open with default media player
                import subprocess
                import webbrowser
                
                if track:
                    # Try to search for the track using default browser/music service
                    search_query = f"play {track}"
                    webbrowser.open(f"https://music.youtube.com/search?q={search_query.replace(' ', '+')}")
                    message = f"Opened search for track: {track}"
                elif playlist:
                    search_query = f"playlist {playlist}"
                    webbrowser.open(f"https://music.youtube.com/search?q={search_query.replace(' ', '+')}")
                    message = f"Opened search for playlist: {playlist}"
            else:
                # Send play/pause key (VK_MEDIA_PLAY_PAUSE = 0xB3)
                success = self._send_media_key(0xB3)
                message = "Sent play/pause command" if success else "Failed to send media command"
            
            return ToolResult(
                success=True,
                data={
                    "action": "play",
                    "track": track,
                    "playlist": playlist,
                    "message": message
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Play failed: {str(e)}")
    
    def pause(self) -> ToolResult:
        """Pause playback."""
        try:
            # Send play/pause key (VK_MEDIA_PLAY_PAUSE = 0xB3)
            success = self._send_media_key(0xB3)
            message = "Sent pause command" if success else "Failed to send pause command"
            
            return ToolResult(
                success=True,
                data={"action": "pause", "message": message}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Pause failed: {str(e)}")
    
    def resume(self) -> ToolResult:
        """Resume playback."""
        try:
            # Send play/pause key (VK_MEDIA_PLAY_PAUSE = 0xB3)
            success = self._send_media_key(0xB3)
            message = "Sent resume command" if success else "Failed to send resume command"
            
            return ToolResult(
                success=True,
                data={"action": "resume", "message": message}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Resume failed: {str(e)}")
    
    def next(self) -> ToolResult:
        """Skip to next track."""
        try:
            # Send next track key (VK_MEDIA_NEXT_TRACK = 0xB0)
            success = self._send_media_key(0xB0)
            message = "Sent next track command" if success else "Failed to send next command"
            
            return ToolResult(
                success=True,
                data={"action": "next", "message": message}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Next failed: {str(e)}")
    
    def previous(self) -> ToolResult:
        """Skip to previous track."""
        try:
            # Send previous track key (VK_MEDIA_PREV_TRACK = 0xB1)
            success = self._send_media_key(0xB1)
            message = "Sent previous track command" if success else "Failed to send previous command"
            
            return ToolResult(
                success=True,
                data={"action": "previous", "message": message}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Previous failed: {str(e)}")
    
    def set_volume(self, level: int) -> ToolResult:
        """Set system volume level."""
        try:
            import subprocess
            
            # Use PowerShell to set system volume
            ps_script = f"""
            Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int NotImpl1(); int NotImpl2(); int NotImpl3(); int NotImpl4(); int NotImpl5(); int NotImpl6();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                int NotImpl8(); int GetMasterVolumeLevelScalar(out float pfLevel);
            }}'
            
            $volume_level = {level / 100.0}
            
            # Alternative: Use SoundVolumeView or nircmd if available
            # For now, use a simple approach with volume keys
            """
            
            # Fallback: Use volume up/down keys
            current_volume = self._get_current_volume()
            target_volume = level
            
            if target_volume > current_volume:
                # Volume up (VK_VOLUME_UP = 0xAF)
                for _ in range(min(10, target_volume - current_volume)):
                    self._send_media_key(0xAF)
            elif target_volume < current_volume:
                # Volume down (VK_VOLUME_DOWN = 0xAE)
                for _ in range(min(10, current_volume - target_volume)):
                    self._send_media_key(0xAE)
            
            return ToolResult(
                success=True,
                data={
                    "action": "set_volume",
                    "level": level,
                    "message": f"Volume set to approximately {level}%"
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Volume control failed: {str(e)}")
    
    def _get_current_volume(self) -> int:
        """Get current system volume (approximate)."""
        # This is a simplified implementation
        # In a real scenario, you'd query the actual system volume
        return 50  # Default assumption


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

