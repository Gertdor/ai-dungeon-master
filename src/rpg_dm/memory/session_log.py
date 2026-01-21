"""Session logging for tracking game events and history."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..config import get_config


class EventType(str, Enum):
    """Types of events that can be logged."""

    NARRATION = "narration"  # DM narration
    PLAYER_ACTION = "player_action"  # Player declares an action
    DICE_ROLL = "dice_roll"  # Dice roll result
    NPC_ACTION = "npc_action"  # NPC takes action
    NPC_DIALOGUE = "npc_dialogue"  # NPC speaks
    SYSTEM = "system"  # System messages (session start/end, etc.)
    TOOL_CALL = "tool_call"  # Agent tool usage
    STATE_CHANGE = "state_change"  # Game state changes


class Event(BaseModel):
    """A single event in the game session."""

    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: EventType
    actor: Optional[str] = None  # Who performed the action (player name, NPC name, "DM", "system")
    content: str  # Main content of the event
    metadata: dict[str, Any] = Field(default_factory=dict)  # Additional structured data

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor": self.actor,
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=EventType(data["event_type"]),
            actor=data.get("actor"),
            content=data["content"],
            metadata=data.get("metadata", {}),
        )


class Scene(BaseModel):
    """A scene within a game session - a narrative unit containing related events."""

    scene_id: str
    title: Optional[str] = None
    location: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    events: list[Event] = Field(default_factory=list)
    summary: Optional[str] = None
    is_active: bool = True

    def add_event(self, event: Event) -> None:
        """Add an event to this scene."""
        self.events.append(event)

        # Track participants
        if event.actor and event.actor not in self.participants:
            self.participants.append(event.actor)

    def close(self, summary: Optional[str] = None) -> None:
        """Close the scene, marking it as complete."""
        self.end_time = datetime.now()
        self.is_active = False
        if summary:
            self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        """Convert scene to dictionary for serialization."""
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "location": self.location,
            "participants": self.participants,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "events": [event.to_dict() for event in self.events],
            "summary": self.summary,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        """Create scene from dictionary."""
        return cls(
            scene_id=data["scene_id"],
            title=data.get("title"),
            location=data.get("location"),
            participants=data.get("participants", []),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            events=[Event.from_dict(e) for e in data.get("events", [])],
            summary=data.get("summary"),
            is_active=data.get("is_active", True),
        )


class SessionLog:
    """Manages logging of game session with scenes and events."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize session log.

        Args:
            session_id: Unique identifier for this session. If None, generates from timestamp.
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = get_config()
        self.scenes: list[Scene] = []
        self.current_scene: Optional[Scene] = None

        # Create sessions directory
        self.sessions_dir = self.config.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Session file path
        self.session_file = self.sessions_dir / f"{self.session_id}.json"

        # Load existing session if file exists
        if self.session_file.exists():
            self._load_session()
        else:
            # Start with a default scene for free-form play
            self.start_scene()

    def start_scene(
        self,
        title: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Scene:
        """Start a new scene.

        Args:
            title: Optional scene title
            location: Optional scene location

        Returns:
            The newly created Scene
        """
        # Close previous scene if active
        if self.current_scene and self.current_scene.is_active:
            self.current_scene.close()

        # Create new scene
        scene_id = f"scene_{len(self.scenes) + 1}"
        scene = Scene(
            scene_id=scene_id,
            title=title,
            location=location,
        )

        self.scenes.append(scene)
        self.current_scene = scene
        self._save_session()

        return scene

    def end_scene(self, summary: Optional[str] = None) -> None:
        """End the current scene.

        Args:
            summary: Optional summary of what happened in the scene
        """
        if self.current_scene and self.current_scene.is_active:
            self.current_scene.close(summary)
            self._save_session()

    def log_event(
        self,
        event_type: EventType,
        content: str,
        actor: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Event:
        """Log a new event to the current scene.

        Args:
            event_type: Type of event
            content: Event content
            actor: Who performed the action
            metadata: Additional structured data

        Returns:
            The created Event
        """
        event = Event(
            event_type=event_type,
            content=content,
            actor=actor,
            metadata=metadata or {},
        )

        # Ensure we have an active scene
        if not self.current_scene or not self.current_scene.is_active:
            self.start_scene()

        self.current_scene.add_event(event)
        self._save_session()
        return event

    def get_all_events(self) -> list[Event]:
        """Get all events from all scenes in chronological order."""
        all_events = []
        for scene in self.scenes:
            all_events.extend(scene.events)
        return all_events

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        actor: Optional[str] = None,
        limit: Optional[int] = None,
        scene_id: Optional[str] = None,
    ) -> list[Event]:
        """Retrieve events with optional filtering.

        Args:
            event_type: Filter by event type
            actor: Filter by actor
            limit: Maximum number of events to return (most recent first)
            scene_id: Filter by specific scene

        Returns:
            List of matching events
        """
        # Get events from specified scene or all scenes
        if scene_id:
            scene = next((s for s in self.scenes if s.scene_id == scene_id), None)
            filtered = scene.events if scene else []
        else:
            filtered = self.get_all_events()

        # Apply filters
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if actor:
            filtered = [e for e in filtered if e.actor == actor]

        # Return most recent first
        filtered = list(reversed(filtered))

        if limit:
            filtered = filtered[:limit]

        return filtered

    def get_context_for_llm(
        self,
        include_current_scene_events: int = 20,
        include_previous_scenes: int = 2,
        include_older_summaries: bool = True,
    ) -> str:
        """Get context string optimized for LLM consumption.

        Args:
            include_current_scene_events: Number of events from current scene
            include_previous_scenes: Number of previous scenes to include full events
            include_older_summaries: Include summaries of older scenes

        Returns:
            Formatted context string
        """
        lines = []

        # Get scene indices
        current_idx = len(self.scenes) - 1 if self.scenes else -1

        if current_idx < 0:
            return "No events yet."

        # Include older scene summaries
        if include_older_summaries and current_idx >= include_previous_scenes + 1:
            lines.append("## Earlier Events")
            for i in range(0, current_idx - include_previous_scenes):
                scene = self.scenes[i]
                title = scene.title or f"Scene {i + 1}"
                if scene.summary:
                    lines.append(f"**{title}**: {scene.summary}")
                else:
                    lines.append(f"**{title}**: {len(scene.events)} events")
            lines.append("")

        # Include full events from recent previous scenes
        if include_previous_scenes > 0:
            start_idx = max(0, current_idx - include_previous_scenes)
            for i in range(start_idx, current_idx):
                scene = self.scenes[i]
                title = scene.title or f"Scene {i + 1}"
                lines.append(f"## {title}")
                if scene.location:
                    lines.append(f"Location: {scene.location}")
                for event in scene.events:
                    actor_str = f"[{event.actor}] " if event.actor else ""
                    lines.append(f"{actor_str}{event.content}")
                lines.append("")

        # Include current scene with more detail
        current_scene = self.scenes[current_idx]
        title = current_scene.title or "Current Scene"
        lines.append(f"## {title}")
        if current_scene.location:
            lines.append(f"Location: {current_scene.location}")

        # Get recent events from current scene
        events = current_scene.events[-include_current_scene_events:]
        for event in events:
            actor_str = f"[{event.actor}] " if event.actor else ""
            lines.append(f"{actor_str}{event.content}")

        return "\n".join(lines)

    def get_recent_context(self, max_events: int = 10) -> str:
        """Get recent events as a formatted string for context.

        Args:
            max_events: Maximum number of recent events to include

        Returns:
            Formatted string of recent events
        """
        recent = self.get_events(limit=max_events)
        if not recent:
            return "No recent events."

        lines = []
        for event in reversed(recent):  # Chronological order
            actor_str = f"[{event.actor}] " if event.actor else ""
            lines.append(f"{actor_str}{event.content}")

        return "\n".join(lines)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for the session.

        Returns:
            Dictionary with session statistics
        """
        all_events = self.get_all_events()

        if not all_events:
            return {
                "session_id": self.session_id,
                "scene_count": 0,
                "event_count": 0,
                "start_time": None,
                "end_time": None,
            }

        event_types = {}
        for event in all_events:
            event_types[event.event_type.value] = event_types.get(event.event_type.value, 0) + 1

        return {
            "session_id": self.session_id,
            "scene_count": len(self.scenes),
            "active_scene": self.current_scene.title or self.current_scene.scene_id
            if self.current_scene
            else None,
            "event_count": len(all_events),
            "start_time": all_events[0].timestamp.isoformat(),
            "end_time": all_events[-1].timestamp.isoformat(),
            "event_types": event_types,
            "scenes": [
                {
                    "id": scene.scene_id,
                    "title": scene.title,
                    "location": scene.location,
                    "event_count": len(scene.events),
                    "is_active": scene.is_active,
                }
                for scene in self.scenes
            ],
        }

    def _save_session(self) -> None:
        """Save session to disk."""
        data = {
            "session_id": self.session_id,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "current_scene_id": self.current_scene.scene_id if self.current_scene else None,
        }

        with open(self.session_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_session(self) -> None:
        """Load session from disk."""
        with open(self.session_file) as f:
            data = json.load(f)

        self.scenes = [Scene.from_dict(scene_data) for scene_data in data.get("scenes", [])]

        # Restore current scene reference
        current_scene_id = data.get("current_scene_id")
        if current_scene_id:
            self.current_scene = next(
                (s for s in self.scenes if s.scene_id == current_scene_id), None
            )
