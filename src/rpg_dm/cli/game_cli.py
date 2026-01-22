"""CLI interface for running RPG sessions."""

import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
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


class CommandResult(Enum):
    """Result of handling a command."""
    REGULAR_ACTION = "regular"  # Not a command, process as game action
    HANDLED = "handled"  # Command was handled, continue game loop
    EXIT_TO_MENU = "exit"  # Return to main menu
    QUIT_APP = "quit"  # Shut down the application


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

Commands during gameplay:
- Type your actions naturally to interact with the game
- `/help` - Show available commands
- `/exit` - Return to main menu
- `/quit` - Quit the application
- `/roll <notation>` - Roll dice (e.g., /roll d20, /roll 2d6+3)
- `/state` - Show current game state
- `/save` - Save the current session

Let's begin your adventure!
"""
        self.console.print(Markdown(welcome_text))

    def show_main_menu(self) -> str:
        """Show main menu and get user choice.

        Returns:
            User's menu choice: 'new', 'load', or 'quit'
        """
        self.console.print("\n[bold cyan]Main Menu[/bold cyan]\n")
        self.console.print("[N] Start New Game")
        self.console.print("[L] Load Saved Game")
        self.console.print("[Q] Quit\n")

        choice = Prompt.ask(
            "Choose an option",
            choices=["n", "N", "l", "L", "q", "Q"],
            default="N"
        ).upper()

        choice_map = {
            "N": "new",
            "L": "load",
            "Q": "quit"
        }

        return choice_map.get(choice, "new")

    def list_saved_sessions(self) -> list[str]:
        """List available saved sessions.

        Returns:
            List of session IDs
        """
        data_dir = Path(self.config.data_dir) / "sessions"
        if data_dir.exists():
            return sorted([f.stem for f in data_dir.glob("*.json")], reverse=True)
        return []

    def show_help(self) -> None:
        """Show help message."""
        help_text = """
# Available Commands

## Game Actions
- Just type naturally to interact with the game world
- The DM will respond to your actions and roll dice as needed

## Special Commands
- `/help` - Show this help message
- `/quit` or `/exit` - Save and exit the game
- `/load <session_id>` - Load a saved session from data/sessions/
- `/roll <notation>` - Roll dice manually
  - Examples: `/roll d20`, `/roll 2d6+3`, `/roll 4d6kh3`
- `/state` - Show current game state (location, NPCs, etc.)
- `/save` - Save the current session to disk

## Tips
- Be descriptive in your actions
- The DM manages scenes automatically based on your actions
- Your session is automatically logged and can be resumed later
- Use `/load <session_id>` to continue a previous adventure
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

    def load_session(self, session_id: str) -> bool:
        """Load a saved session.

        Args:
            session_id: Session ID to load

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Load session log
            self.session_log = SessionLog(session_id=session_id)
            self.session_log.load()

            # Create DM agent
            self.dm_agent = DMAgent(
                config=self.config,
                llm_client=self.llm_client,
                session_log=self.session_log,
                dice_roller=self.dice_roller,
            )

            # Try to recreate game state from session metadata
            # For now, create minimal game state
            self.game_state = GameState()

            # Extract character info from session events if available
            # This is a simplified version - could be enhanced
            all_events = self.session_log.get_all_events()
            if all_events:
                # Look for player name in early events
                for event in all_events[:10]:
                    if event.actor and event.actor != "DM" and event.actor != "system":
                        self.game_state.set_player_character(
                            PlayerCharacter(name=event.actor, description="Loaded character")
                        )
                        break

            # Get current location from active scene
            if self.session_log.current_scene:
                if self.session_log.current_scene.location:
                    self.game_state.set_location(self.session_log.current_scene.location)

            self.console.print(f"[green]Session '{session_id}' loaded successfully![/green]")
            self.console.print(f"[cyan]Found {len(self.session_log.scenes)} scenes with {len(all_events)} events.[/cyan]")
            return True

        except FileNotFoundError:
            self.console.print(f"[red]Session '{session_id}' not found in data/sessions/[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error loading session: {e}[/red]")
            return False

    def handle_command(self, user_input: str) -> CommandResult:
        """Handle special commands.

        Args:
            user_input: User input string

        Returns:
            CommandResult indicating what to do next
        """
        user_input = user_input.strip()

        if user_input == "/quit":
            # Ask if user wants to save
            if self.session_log:
                save_choice = Prompt.ask(
                    "Save before quitting? [Y/n]",
                    choices=["y", "Y", "n", "N", ""],
                    default="Y"
                ).upper()
                if save_choice != "N":
                    self.session_log.save()
                    self.console.print("[green]Session saved.[/green]")
            self.console.print("\n[yellow]Thanks for playing![/yellow]")
            return CommandResult.QUIT_APP

        elif user_input == "/exit":
            # Ask if user wants to save
            if self.session_log:
                save_choice = Prompt.ask(
                    "Save before returning to menu? [Y/n]",
                    choices=["y", "Y", "n", "N", ""],
                    default="Y"
                ).upper()
                if save_choice != "N":
                    self.session_log.save()
                    self.console.print("[green]Session saved.[/green]")
            return CommandResult.EXIT_TO_MENU

        elif user_input == "/help":
            self.show_help()
            return CommandResult.HANDLED

        elif user_input == "/state":
            if self.game_state:
                state_summary = self.game_state.get_state_summary()
                self.console.print(Panel(state_summary, title="Game State", border_style="cyan"))
            else:
                self.console.print("[yellow]No game state available.[/yellow]")
            return CommandResult.HANDLED

        elif user_input == "/save":
            if self.session_log:
                self.session_log.save()
                self.console.print("[green]Session saved successfully![/green]")
            else:
                self.console.print("[yellow]No session to save.[/yellow]")
            return CommandResult.HANDLED

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
            return CommandResult.HANDLED

        return CommandResult.REGULAR_ACTION

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

    def run_game_session(self) -> CommandResult:
        """Run a single game session.

        Returns:
            CommandResult indicating why the session ended
        """
        # Get initial DM narration (only for new games with setting)
        if self.game_state and self.game_state.get_world_state("starting_setting"):
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
                    result = self.handle_command(user_input)
                    if result == CommandResult.QUIT_APP:
                        return CommandResult.QUIT_APP
                    elif result == CommandResult.EXIT_TO_MENU:
                        return CommandResult.EXIT_TO_MENU
                    elif result == CommandResult.HANDLED:
                        continue
                    # If REGULAR_ACTION, fall through to process as action

                # Process normal turn (if not a command or if command returned REGULAR_ACTION)
                if not user_input.startswith("/") or result == CommandResult.REGULAR_ACTION:
                    self.process_turn(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Game interrupted.[/yellow]")
                if self.session_log:
                    save_choice = Prompt.ask(
                        "Save before exiting? [Y/n]",
                        choices=["y", "Y", "n", "N", ""],
                        default="Y"
                    ).upper()
                    if save_choice != "N":
                        self.session_log.save()
                        self.console.print("[green]Session saved.[/green]")
                return CommandResult.EXIT_TO_MENU
            except EOFError:
                return CommandResult.EXIT_TO_MENU

    def run(self) -> None:
        """Run the main application loop with menu."""
        self.show_welcome()

        # Main application loop
        while True:
            choice = self.show_main_menu()

            if choice == "quit":
                break

            elif choice == "new":
                # Setup new game
                self.setup_game()
                # Run game session
                result = self.run_game_session()
                if result == CommandResult.QUIT_APP:
                    break
                # Otherwise, return to menu

            elif choice == "load":
                # Show available sessions
                sessions = self.list_saved_sessions()
                if sessions:
                    self.console.print("\n[cyan]Available sessions (most recent first):[/cyan]")
                    for i, session in enumerate(sessions[:15], 1):  # Show last 15
                        self.console.print(f"  {i}. {session}")
                    self.console.print()

                    session_id = Prompt.ask("Enter session ID to load (or press Enter to cancel)", default="")
                    if session_id and self.load_session(session_id):
                        # Show recent context
                        recent_events = self.session_log.get_recent_context(num_events=5)
                        if recent_events:
                            self.console.print("\n[bold cyan]Recent Events:[/bold cyan]")
                            self.console.print(recent_events)
                            self.console.print()
                        # Run loaded game session
                        result = self.run_game_session()
                        if result == CommandResult.QUIT_APP:
                            break
                    elif session_id:
                        self.console.print("[yellow]Failed to load session.[/yellow]")
                else:
                    self.console.print("[yellow]No saved sessions found.[/yellow]")
                    input("\nPress Enter to continue...")


def main() -> None:
    """Main entry point for the CLI."""
    cli = GameCLI()
    cli.run()


if __name__ == "__main__":
    main()
