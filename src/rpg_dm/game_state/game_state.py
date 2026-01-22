"""Game state management for tracking characters and world state."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PlayerCharacter(BaseModel):
    """Represents a player character."""

    name: str
    description: Optional[str] = None
    stats: dict[str, Any] = Field(default_factory=dict)
    inventory: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_item(self, item: str) -> None:
        """Add an item to inventory.

        Args:
            item: Item to add
        """
        self.inventory.append(item)

    def remove_item(self, item: str) -> bool:
        """Remove an item from inventory.

        Args:
            item: Item to remove

        Returns:
            True if item was removed, False if not found
        """
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def add_note(self, note: str) -> None:
        """Add a note to the character.

        Args:
            note: Note to add
        """
        self.notes.append(note)


class GameState(BaseModel):
    """Manages the overall game state."""

    player_character: Optional[PlayerCharacter] = None
    current_location: Optional[str] = None
    world_state: dict[str, Any] = Field(default_factory=dict)
    active_npcs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def set_player_character(self, character: PlayerCharacter) -> None:
        """Set the player character.

        Args:
            character: Player character
        """
        self.player_character = character

    def set_location(self, location: str) -> None:
        """Set the current location.

        Args:
            location: Location name
        """
        self.current_location = location

    def update_world_state(self, key: str, value: Any) -> None:
        """Update a world state variable.

        Args:
            key: State variable name
            value: State variable value
        """
        self.world_state[key] = value

    def get_world_state(self, key: str, default: Any = None) -> Any:
        """Get a world state variable.

        Args:
            key: State variable name
            default: Default value if key not found

        Returns:
            State variable value or default
        """
        return self.world_state.get(key, default)

    def add_npc(self, name: str, data: dict[str, Any]) -> None:
        """Add or update an NPC.

        Args:
            name: NPC name
            data: NPC data
        """
        self.active_npcs[name] = data

    def get_npc(self, name: str) -> Optional[dict[str, Any]]:
        """Get NPC data.

        Args:
            name: NPC name

        Returns:
            NPC data or None if not found
        """
        return self.active_npcs.get(name)

    def remove_npc(self, name: str) -> bool:
        """Remove an NPC.

        Args:
            name: NPC name

        Returns:
            True if removed, False if not found
        """
        if name in self.active_npcs:
            del self.active_npcs[name]
            return True
        return False

    def get_state_summary(self) -> str:
        """Get a summary of the game state.

        Returns:
            String summary of game state
        """
        lines = []

        if self.player_character:
            lines.append(f"Player: {self.player_character.name}")
            if self.player_character.description:
                lines.append(f"  {self.player_character.description}")

        if self.current_location:
            lines.append(f"Location: {self.current_location}")

        if self.active_npcs:
            lines.append(f"Active NPCs: {', '.join(self.active_npcs.keys())}")

        if self.world_state:
            lines.append("World State:")
            for key, value in self.world_state.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines) if lines else "No game state"
