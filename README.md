# Tabletop RPG DM Agent System

An agentic AI Dungeon Master system for tabletop RPGs, featuring intelligent narrative generation, session memory, and tool-based interactions.

**Platform:** Linux (MVP)

## Features (MVP)

- **Interactive Menu System**: Start new games, load saved sessions, or quit
- **AI-Powered DM**: Intelligent dungeon master with Claude 4.5 Sonnet
- **Streaming Narration**: Real-time text generation for immersive gameplay
- **Session Management**: Automatic session logging with scene hierarchy
- **Player-Defined Settings**: Choose your starting location and scenario
- **Dice Rolling**: Support for standard notation (d20, 2d6+3, 4d6kh3, advantage/disadvantage)
- **Arbitrary Dice Sizes**: Roll d3, d7, d25, d100, or any other die size
- **Game State Tracking**: Character stats, inventory, NPCs, and world state
- **Tool Calling**: DM automatically rolls dice and manages scenes
- **Save/Load System**: Resume adventures anytime
- **Game System Agnostic**: Core works with any RPG system

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using Poetry (recommended)

```bash
poetry install
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your OpenRouter API key to `.env`:
```
OPENROUTER_API_KEY=your_api_key_here
```

3. (Optional) Customize model settings in `.env`

## Usage

### Starting the Game

```bash
# With poetry (recommended)
poetry run rpg-dm

# Or with pip
python -m rpg_dm.cli.game_cli
```

### Main Menu

When you start the game, you'll see the main menu:
- **[N] Start New Game**: Create a new character and adventure
- **[L] Load Saved Game**: Continue a previous session
- **[Q] Quit**: Exit the application

### Creating a New Game

1. Enter your character's name
2. Describe your character (optional)
3. Describe where and how you want the adventure to begin
4. The DM will set the opening scene based on your description

### Commands During Gameplay

While playing:
- **Type naturally**: Describe your actions and the DM will respond
- `/help` - Show available commands
- `/roll <notation>` - Roll dice manually
  - Examples: `/roll d20`, `/roll 2d6+3`, `/roll 4d6kh3`
- `/state` - Show current game state (location, NPCs, etc.)
- `/save` - Manually save the session
- `/exit` - Return to main menu (prompts to save)
- `/quit` - Quit application (prompts to save)

## Development

### Setup Development Environment

```bash
poetry install --with dev
```

### Run Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run ruff check src/
```

## Architecture

See [architecture_docs/](architecture_docs/) for detailed design documentation:
- [System Requirements](architecture_docs/01_system_requirements.md)
- [Tools Catalog](architecture_docs/02_tools_catalog.md)
- [Architecture Outline](architecture_docs/03_architecture_outline.md)

## Project Structure

```
src/rpg_dm/
├── __init__.py
├── config.py           # Configuration management
├── llm/                # LLM client wrapper (OpenRouter/OpenAI compatible)
├── memory/             # Session logging with scene hierarchy
├── utilities/          # Dice rolling and other utilities
├── agents/             # DM agent with tool calling
├── game_state/         # Game state management (characters, NPCs, world)
└── cli/                # Command-line interface with menu system

gamesystems/
└── blades_in_the_dark/ # Game system specific content

data/                   # Session logs and game state (created at runtime)
tests/                  # Comprehensive test suite
```