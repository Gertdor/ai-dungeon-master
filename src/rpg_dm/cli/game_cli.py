"""CLI interface for running RPG sessions."""

import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from rpg_dm.agents import DMAgent
from rpg_dm.config import get_config
from rpg_dm.game_state import GameState, PlayerCharacter
from rpg_dm.llm import LLMClient
from rpg_dm.memory import SessionLog
from rpg_dm.utilities.dice import DiceRoller


class GameCLI:
    """Command-line interface for the RPG game."""

    def __init__(self):
        """Initialize the game CLI."""
        self.console = Console()
        self.config = get_config()
        self.llm_client = LLMClient(self.config)
        self.dice_roller = DiceRoller()
        self.session_log: Optional[SessionLog] = None
        self.game_state: Optional[GameState] = None
        self.dm_agent: Optional[DMAgent] = None

    def show_welcome(self) -> None:
        """Show welcome message."""
        welcome_text = """
# Welcome to the AI Dungeon Master

An intelligent tabletop RPG experience powered by AI.

Commands:
- Type your actions naturally to interact with the game
- `/help` - Show available commands
- `/quit` - Exit the game
- `/scene` - Start a new scene
- `/roll <notation>` - Roll dice (e.g., /roll d20, /roll 2d6+3)
- `/state` - Show current game state
- `/save` - Save the current session

Let's begin your adventure!
"""
        self.console.print(Markdown(welcome_text))

    def show_help(self) -> None:
        """Show help message."""
        help_text = """
# Available Commands

## Game Actions
- Just type naturally to interact with the game world
- The DM will respond to your actions and roll dice as needed

## Special Commands
- `/help` - Show this help message
- `/quit` or `/exit` - Exit the game
- `/scene <title>` - Start a new scene with a title
- `/roll <notation>` - Roll dice manually
  - Examples: `/roll d20`, `/roll 2d6+3`, `/roll 4d6kh3`
- `/state` - Show current game state (location, NPCs, etc.)
- `/save` - Save the current session to disk

## Tips
- Be descriptive in your actions
- The DM has access to dice rolling and scene management
- Your session is automatically logged and can be resumed later
"""
        self.console.print(Markdown(help_text))

    def setup_game(self) -> None:
        """Set up a new game session."""
        self.console.print("\n[bold cyan]Game Setup[/bold cyan]\n")

        # Get player character name
        character_name = Prompt.ask("What is your character's name?", default="Hero")

        # Get character description
        character_desc = Prompt.ask(
            "Describe your character (optional)", default="A brave adventurer"
        )

        # Get starting setting from player
        self.console.print("\n[bold cyan]Setting[/bold cyan]")
        setting_desc = Prompt.ask(
            "Describe where and how you want the adventure to begin",
            default="A mysterious tavern in a medieval fantasy world"
        )

        # Create player character
        player_character = PlayerCharacter(name=character_name, description=character_desc)

        # Create game state
        self.game_state = GameState()
        self.game_state.set_player_character(player_character)

        # Store the setting in game state
        self.game_state.update_world_state("starting_setting", setting_desc)

        # Create session log
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = SessionLog(session_id=session_id)

        # Create DM agent
        self.dm_agent = DMAgent(
            config=self.config,
            llm_client=self.llm_client,
            session_log=self.session_log,
            dice_roller=self.dice_roller,
        )

        # Start initial scene with player's setting
        self.session_log.start_scene(
            title="The Adventure Begins", location=setting_desc
        )

        self.console.print(f"\n[green]Welcome, {character_name}![/green]\n")

    def handle_command(self, user_input: str) -> bool:
        """Handle special commands.

        Args:
            user_input: User input string

        Returns:
            True if command was handled, False if it's a regular action
        """
        user_input = user_input.strip()

        if user_input in ["/quit", "/exit"]:
            # Save the session before quitting
            if self.session_log:
                self.session_log.save()
            self.console.print("\n[yellow]Thanks for playing! Your session has been saved.[/yellow]")
            return True

        elif user_input == "/help":
            self.show_help()
            return True

        elif user_input == "/state":
            if self.game_state:
                state_summary = self.game_state.get_state_summary()
                self.console.print(Panel(state_summary, title="Game State", border_style="cyan"))
            else:
                self.console.print("[yellow]No game state available.[/yellow]")
            return True

        elif user_input == "/save":
            if self.session_log:
                self.session_log.save()
                self.console.print("[green]Session saved successfully![/green]")
            else:
                self.console.print("[yellow]No session to save.[/yellow]")
            return True

        elif user_input.startswith("/scene "):
            scene_title = user_input[7:].strip()
            if scene_title and self.session_log:
                # End current scene
                self.session_log.end_scene(summary="Scene ended by player")
                # Start new scene
                self.session_log.start_scene(title=scene_title, location="To be determined")
                self.console.print(f"[green]Started new scene: {scene_title}[/green]")
            else:
                self.console.print("[yellow]Please provide a scene title: /scene <title>[/yellow]")
            return True

        elif user_input.startswith("/roll "):
            notation = user_input[6:].strip()
            if notation:
                try:
                    result = self.dice_roller.roll(notation)
                    self.console.print(f"[bold cyan]Roll:[/bold cyan] {result.details}")
                    if self.session_log:
                        self.session_log.log_event(
                            event_type="dice_roll",
                            content=f"Player rolled: {result.details}",
                            actor="Player",
                            metadata={"notation": notation, "total": result.total},
                        )
                except ValueError as e:
                    self.console.print(f"[red]Invalid dice notation: {e}[/red]")
            else:
                self.console.print("[yellow]Please provide dice notation: /roll <notation>[/yellow]")
            return True

        return False

    def process_turn(self, user_input: str) -> None:
        """Process a single turn.

        Args:
            user_input: User input
        """
        if not self.dm_agent:
            self.console.print("[red]Game not initialized![/red]")
            return

        # Show player input
        if self.game_state and self.game_state.player_character:
            player_name = self.game_state.player_character.name
            self.console.print(f"\n[bold green]{player_name}:[/bold green] {user_input}\n")

        # Get DM response with streaming
        self.console.print("[bold magenta]DM:[/bold magenta] ", end="")

        try:
            for chunk in self.dm_agent.respond_stream(user_input):
                self.console.print(chunk, end="")
                sys.stdout.flush()

            self.console.print("\n")  # New line after streaming

        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]\n")

    def run(self) -> None:
        """Run the main game loop."""
        self.show_welcome()

        # Setup game
        self.setup_game()

        # Get initial DM narration with the player's setting
        setting = self.game_state.get_world_state("starting_setting", "an unknown location")
        character_name = self.game_state.player_character.name if self.game_state.player_character else "the hero"
        character_desc = self.game_state.player_character.description if self.game_state.player_character else "an adventurer"

        initial_prompt = f"""Begin the adventure for {character_name}, {character_desc}.

Setting: {setting}

Describe the opening scene vividly, incorporating the setting the player described. Set the atmosphere and present an initial situation or hook. End by asking the player what they do."""

        self.console.print("\n[bold magenta]DM:[/bold magenta] ", end="")
        try:
            for chunk in self.dm_agent.respond_stream(initial_prompt):
                self.console.print(chunk, end="")
                sys.stdout.flush()
            self.console.print("\n")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]\n")

        # Main game loop
        while True:
            try:
                # Get player input
                user_input = Prompt.ask("\n[bold cyan]What do you do?[/bold cyan]").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        if user_input in ["/quit", "/exit"]:
                            break
                        continue

                # Process normal turn
                self.process_turn(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Game interrupted. Saving session...[/yellow]")
                if self.session_log:
                    self.session_log.save()
                break
            except EOFError:
                break


def main() -> None:
    """Main entry point for the CLI."""
    cli = GameCLI()
    cli.run()


if __name__ == "__main__":
    main()
