# Tabletop RPG DM Agent System

An agentic AI Dungeon Master system for tabletop RPGs, starting with Blades in the Dark.

**Platform:** Linux (MVP)

## Features (MVP)

- Single-player text-based interface
- AI-powered DM agent with narrative generation
- Simple memory system (session logging)
- Dice rolling with standard notation
- Manual turn management
- Game system agnostic core (with Blades in the Dark support)

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

### Run the DM

```bash
# With pip
python -m rpg_dm.cli

# With poetry
poetry run rpg-dm
```

### Basic Commands

During a game session:
- Type your actions and the DM will respond
- `/roll 2d6` - Roll dice
- `/help` - Show available commands
- `/quit` - End the session

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
├── llm/                # LLM client wrapper
├── memory/             # Memory and session logging
├── utilities/          # Dice rolling and other utilities
├── agents/             # DM and NPC agents
├── state/              # Game state management
└── cli.py              # Command-line interface

gamesystems/
└── blades_in_the_dark/ # Game system specific content

data/                   # Session logs and game state (created at runtime)
```