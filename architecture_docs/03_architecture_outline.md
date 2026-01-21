# Architecture Outline - Tabletop RPG DM Agent System

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Player Interface Layer                   │
│  (Web UI, CLI, Discord Bot, VTT Integration, etc.)          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Orchestrator Agent                          │
│  - Turn management                                           │
│  - Agent coordination                                        │
│  - Context assembly and distribution                         │
│  - Flow control and interruption handling                    │
└─────┬──────────────┬──────────────┬────────────────────────┘
      │              │              │
      │              │              └──────────────┐
      │              │                             │
┌─────▼──────┐  ┌───▼────────┐  ┌─────────────┐ │ ┌──────────────┐
│ DM Agent   │  │ NPC Agents │  │  PC Agents  │ │ │  Tool Layer  │
│            │  │ (Dynamic)  │  │  (Optional) │ │ │              │
└─────┬──────┘  └───┬────────┘  └─────┬───────┘ │ └──────┬───────┘
      │             │                  │         │        │
      └─────────────┴──────────────────┴─────────┼────────┘
                                                  │
┌─────────────────────────────────────────────────▼─────────┐
│                    Shared Services Layer                   │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │   Memory     │ │   Rules     │ │    Content       │   │
│  │   System     │ │   Engine    │ │    Generator     │   │
│  └──────────────┘ └─────────────┘ └──────────────────┘   │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │   State      │ │   Dice      │ │    Knowledge     │   │
│  │   Manager    │ │   Roller    │ │    Graph         │   │
│  └──────────────┘ └─────────────┘ └──────────────────┘   │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    Persistence Layer                        │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │   Session    │ │   Campaign  │ │    Character     │   │
│  │   Database   │ │   Database  │ │    Database      │   │
│  └──────────────┘ └─────────────┘ └──────────────────┘   │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │   Vector     │ │   Rules     │ │    Asset         │   │
│  │   Store      │ │   Store     │ │    Storage       │   │
│  └──────────────┘ └─────────────┘ └──────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Player Interface Layer

**Purpose**: Handle human input/output and platform-specific interactions.

**Responsibilities**:
- Render narrative text and game state to players
- Capture player commands and decisions
- Display character sheets, maps, and visual aids
- Handle authentication and session management
- Provide safety tools and settings
- Support multiple simultaneous players

**Technology Options**:
- Web interface (React, Vue, Svelte)
- Terminal CLI (for text-based play)
- Discord/Slack bot integration
- VTT platform plugins (Roll20, Foundry)
- Voice interface (future consideration)

### 2. Orchestrator Agent

**Purpose**: Coordinate all agents and manage information flow.

**Core Responsibilities**:
- **Turn Management**: Determine which agent acts next
- **Context Assembly**: Build appropriate context windows for each agent
- **Agent Spawning**: Create/destroy NPC agents dynamically
- **Information Gating**: Ensure agents only access appropriate information
- **Conflict Resolution**: Handle contradictions between agents
- **State Synchronization**: Keep all agents aligned on world state

**Key Algorithms**:
- **Turn Priority Queue**: Manages initiative and action order
- **Context Relevance Ranking**: Scores memories/info by relevance
- **Token Budget Management**: Allocates context space efficiently
- **Consistency Checker**: Validates actions don't contradict established facts

**State Tracked**:
- Current turn holder
- Active agents and their contexts
- Pending interruptions and OOC requests
- Turn history for rollback support

### 3. DM Agent

**Purpose**: Primary world authority and narrative driver.

**Responsibilities**:
- Generate and describe scenes, environments, outcomes
- Control unnamed NPCs and monsters
- Make rulings and interpret mechanics
- Manage pacing and narrative flow
- Create encounters and challenges
- Respond to unexpected player actions
- Maintain genre and tone consistency

**Prompting Strategy**:
- System prompt defines DM role, campaign setting, tone
- Context includes recent events, active NPCs, location, plot threads
- Has access to full world state and all memories
- Can query player preferences and safety boundaries

**Decision-Making**:
- Balances challenge, story, and player agency
- Considers genre conventions and table expectations
- Adapts difficulty based on party state
- Recognizes when to say "yes, and..." vs "no, but..."

### 4. NPC Agent Pool

**Purpose**: Provide individualized, believable NPC behavior.

**Architecture**:
- **Dynamic Instantiation**: NPCs only become agents when relevant
- **Tiered System**:
  - **Major NPCs**: Full agent with persistent context
  - **Minor NPCs**: Lightweight agent, created on-demand
  - **Background NPCs**: Handled by DM directly

**Individual NPC Context**:
- Character profile (personality, goals, knowledge)
- Personal memory bank (conversations, observations)
- Relationship map (feelings toward PCs and other NPCs)
- Current emotional state and objectives

**Knowledge Isolation**:
- NPCs only know what they've learned in-fiction
- Cannot access DM secrets or other NPC thoughts
- Knowledge propagates through explicit conversations
- Tracks sources of information (hearsay vs direct)

**Lifecycle**:
1. Created when NPC first becomes relevant
2. Loaded with profile and relevant memories
3. Activated when interaction occurs
4. Summarized and stored when interaction ends
5. Reactivated if NPC appears again

### 5. PC Agent (Optional)

**Purpose**: Assist players with character management and options.

**Use Cases**:
- New players who need guidance
- Complex character classes with many options
- Automation of routine tracking (resources, conditions)
- Recall of character-specific information

**Important Constraints**:
- Never makes decisions for player
- Provides suggestions, not commands
- Can be disabled by player preference
- Transparent about what it's doing

### 6. Tool Layer

**Purpose**: Provide atomic, reliable functions for agents to use.

**Tool Categories**:
See detailed Tool Catalog document for full listing.

**Tool Execution Flow**:
1. Agent requests tool via structured call
2. Orchestrator validates permissions
3. Tool executes with current state
4. Results returned to agent
5. State changes logged and propagated

**Tool Design**:
- Idempotent where possible
- Clear success/failure indication
- Rollback support for state changes
- Performance metrics tracking

## Shared Services Layer

### Memory System

**Purpose**: Store, retrieve, and manage all game history and state.

**Components**:

1. **Session Logger**
   - Timestamped event stream
   - Tagged by type, participants, location
   - Searchable by multiple indices

2. **Memory Summarizer**
   - Compresses old sessions into key facts
   - Maintains detail gradient (recent = detailed, old = summarized)
   - Extracts important plot points and relationships

3. **Memory Retriever**
   - Semantic search across all memories
   - Recency and relevance scoring
   - Fast lookup by entity (NPC, location, item)

4. **Context Window Builder**
   - Assembles memories for agent context
   - Balances recency, relevance, and diversity
   - Respects token budgets

**Storage Strategy**:
- Recent sessions: Full event logs
- Mid-term: Compressed summaries with key details
- Long-term: Distilled facts and relationships
- Critical: Never-forget marked events

**Technology Options**:
- Vector database for semantic search (Pinecone, Weaviate, ChromaDB)
- Relational database for structured queries (PostgreSQL)
- Hybrid approach for best of both

### Rules Engine

**Purpose**: Handle game mechanics and rule interpretation.

**Components**:

1. **Rule Indexer**
   - Searchable rulebook content
   - Organized by topic, keyword, mechanic
   - Includes official rules and house rules

2. **Rule Interpreter**
   - Parses natural language questions
   - Finds relevant rules
   - Explains interactions and edge cases

3. **Mechanic Executor**
   - Calculates modifiers
   - Resolves actions
   - Determines outcomes

**Implementation**:
- Rules stored as structured documents
- Semantic search for rule lookup
- Template-based interpretation
- Can be customized per game system (D&D 5e, Pathfinder, etc.)

### Dice Roller

**Purpose**: Generate random outcomes with proper notation support.

**Features**:
- Standard notation parsing (3d6+2, d20 advantage, etc.)
- Cryptographic randomness option for fairness
- Roll history and statistics
- Support for custom dice mechanics
- Exploding dice, dice pools, success counting

**Interface**:
- Simple API for agents and players
- Returns full roll breakdown
- Logs all rolls with context

### State Manager

**Purpose**: Maintain current world state and ensure consistency.

**Tracks**:
- Current date/time in-game
- Active scene and location
- Character positions and status
- Faction standings and activities
- Environmental conditions
- Resource states (economy, availability)

**Operations**:
- Query current state
- Update state with validation
- Rollback to previous state
- Track state change history
- Notify dependent systems of changes

**Consistency Guarantees**:
- ACID transactions for critical updates
- Conflict detection and resolution
- Audit log of all state changes

### Content Generator

**Purpose**: Create game content on-demand.

**Generators**:
- NPCs (names, traits, stats)
- Locations (descriptions, features, inhabitants)
- Encounters (balanced for party)
- Treasure (level-appropriate loot)
- Plot hooks and complications
- Names (people, places, things)
- Random tables and results

**Quality Control**:
- Consistency with established world
- Appropriate difficulty/level
- Genre and tone matching
- Avoiding repetition

### Knowledge Graph

**Purpose**: Represent relationships between entities in the world.

**Nodes**:
- Characters (PCs, NPCs)
- Locations
- Factions
- Items
- Events
- Concepts (prophecies, legends, etc.)

**Edges**:
- Relationships (friend, enemy, family)
- Spatial (located in, connected to)
- Temporal (happened before, caused by)
- Knowledge (knows about, heard from)
- Ownership (possesses, controls)

**Uses**:
- Quick lookups of relationships
- Ripple effect propagation
- Inconsistency detection
- Generating connection-based plot hooks

**Technology**: Graph database (Neo4j) or graph structure in primary DB

## Persistence Layer

### Session Database

**Schema**:
- Sessions (id, date, title, summary)
- Events (id, session_id, timestamp, type, participants, description)
- Event tags (event_id, tag)

**Queries**:
- Recent events
- Events by participant
- Events by location
- Events by type or tag

### Campaign Database

**Schema**:
- Campaigns (id, name, setting, start_date)
- Plot threads (id, campaign_id, title, status, related_events)
- World state snapshots (id, campaign_id, timestamp, state_data)

### Character Database

**Schema**:
- Characters (id, name, type, stats, personality)
- Character memories (id, character_id, content, timestamp, participants)
- Character relationships (character_id, other_character_id, relationship_type, strength)
- Character knowledge (character_id, fact_id, source, confidence)

### Vector Store

**Purpose**: Enable semantic search across all text content.

**Indexed Content**:
- Session logs
- NPC descriptions
- Location descriptions
- Player notes
- Rule text

**Embedding Strategy**:
- Chunk text into semantic units
- Generate embeddings with model (OpenAI, Sentence Transformers)
- Store with metadata for filtering

### Rules Store

**Content**:
- Core rulebooks (parsed and indexed)
- Supplements and optional rules
- House rules
- Errata and clarifications

**Format**: Structured documents with hierarchy and cross-references

### Asset Storage

**Purpose**: Store binary assets like images, maps, audio.

**Content**:
- Character portraits
- Location maps
- Handouts and props
- Music and ambient sound
- Token images

**Implementation**: Object storage (S3, local filesystem)

## Data Flow Examples

### Example 1: Player Takes Action

```
1. Player: "I persuade the guard to let us through"
   ↓
2. Interface → Orchestrator: Parse player intent
   ↓
3. Orchestrator:
   - Identify relevant context (location, active NPCs, recent events)
   - Determine this requires NPC agent (guard)
   - Build context for guard agent
   ↓
4. Guard Agent activated with context:
   - Guard's personality and goals
   - Guard's memory of PCs
   - Current situation from DM
   - Relationship status
   ↓
5. Guard Agent → Tools:
   - evaluate_trust(PC)
   - check_motivation(let_through vs protect_post)
   - query_knowledge(are_these_people_authorized)
   ↓
6. Guard Agent decides response approach
   ↓
7. DM Agent → Tools:
   - roll_dice(persuasion check)
   ↓
8. DM Agent generates outcome narration based on:
   - Roll result
   - Guard's disposition
   - Situation stakes
   ↓
9. Orchestrator → Guard Agent:
   - remember_interaction(PC persuaded me)
   - update_emotional_state(impressed)
   ↓
10. Orchestrator → Memory System:
    - append_to_session_log(persuasion_event)
    ↓
11. Orchestrator → Interface:
    - Display outcome to players
    - Update world state (guard lets them through)
```

### Example 2: NPC-to-NPC Information Sharing

```
1. DM decides: "The spy reports back to the villain"
   ↓
2. DM Agent → Orchestrator: simulate_npc_conversation(spy, villain)
   ↓
3. Orchestrator:
   - Activate Spy agent with their memories
   - Activate Villain agent with their context
   - Set up conversation framework
   ↓
4. Spy Agent → Tools:
   - retrieve_personal_memory(what_did_I_learn_about_PCs)
   ↓
5. Conversation simulation:
   - Spy describes what they saw
   - Villain asks clarifying questions
   - Spy provides details from memory
   ↓
6. Knowledge propagation:
   - Villain Agent → Tools: remember_interaction(spy_report)
   - Update villain's knowledge state with PC plans
   - Update villain's emotional state (angry, concerned, etc.)
   ↓
7. Orchestrator → Memory System:
   - Log conversation event
   - Update knowledge graph (Villain → knows → PC_plan)
   ↓
8. DM Agent:
   - Generate villain's response/actions based on new info
   - Update faction plans if needed
```

### Example 3: Session Prep and Planning

```
1. DM (human): "Generate three scenario hooks for next session"
   ↓
2. Interface → DM Agent
   ↓
3. DM Agent → Tools:
   - query_campaign_arc(active_plot_threads)
   - query_session_history(unresolved_events)
   - query_world_state(current_location_options)
   ↓
4. DM Agent analyzes:
   - Where PCs are currently
   - What plot threads need attention
   - What would create interesting choices
   ↓
5. DM Agent → Content Generator:
   - generate_scenario_hook(follow_up_to_recent_event)
   - generate_scenario_hook(advance_main_plot)
   - generate_scenario_hook(character_personal_quest)
   ↓
6. DM Agent presents hooks to human DM
   ↓
7. Human DM: "Players chose hook 2"
   ↓
8. DM Agent → Tools:
   - flesh_out_scenario(hook_2)
   ↓
9. DM Agent:
   - Create scene breakdown
   - Generate NPCs needed
   - Create encounters
   - Prepare location descriptions
   ↓
10. DM Agent → Memory System:
    - Store scenario outline
    - Mark plot thread as active
```

## Agent Prompting Strategy

### DM Agent Prompt Structure

```
ROLE: You are the Dungeon Master for a [GENRE] campaign.

CAMPAIGN CONTEXT:
- Setting: [setting_description]
- Tone: [tone_guidance]
- Active Plot Threads: [plot_summary]

CURRENT SITUATION:
- Location: [current_location]
- Present Characters: [pc_list, npc_list]
- Recent Events: [last_3_events]
- Time: [in_game_time]

YOUR RESPONSIBILITIES:
- Describe the world and outcomes of actions
- Play unnamed NPCs and creatures
- Enforce rules fairly and consistently
- Adapt to unexpected player choices
- Maintain narrative pacing and tension

PLAYER PREFERENCES:
- Content boundaries: [safety_info]
- Desired challenge level: [difficulty]
- Playstyle: [roleplay_focused, combat_focused, etc]

TOOLS AVAILABLE:
[tool_descriptions]

CURRENT SCENE:
[scene_description]

What happens next?
```

### NPC Agent Prompt Structure

```
ROLE: You are [NPC_NAME], a [description].

PERSONALITY:
[personality_traits]

GOALS:
- Short-term: [current_goal]
- Long-term: [ultimate_goal]

RELATIONSHIPS:
[relationship_summary]

WHAT YOU KNOW:
[knowledge_summary]

CURRENT SITUATION:
[scene_context_from_npc_perspective]

RECENT MEMORIES:
[last_interactions_with_PCs]

EMOTIONAL STATE: [current_feelings]

CONSTRAINTS:
- You don't know anything beyond what's listed above
- You can't read minds or know PC plans
- You must act according to your personality and goals
- You are not aware you're in a game

TOOLS AVAILABLE:
[limited_npc_tools]

The players are interacting with you. How do you respond?
```

## Scaling Considerations

### Token Management

**Challenge**: Limited context windows for LLM agents.

**Strategies**:
- Compress old memories progressively
- Use embedding search to find only relevant context
- Summarize NPC memories when not active
- Cache frequently accessed information
- Use smaller models for routine tasks

### Agent Lifecycle

**Challenge**: Can't keep all NPCs loaded all the time.

**Solution**:
- Three-tier system:
  - **Hot**: Currently active NPCs (full context)
  - **Warm**: Recent NPCs (summarized state)
  - **Cold**: Historical NPCs (stored in DB, recreated on demand)

### Consistency at Scale

**Challenge**: Multiple agents making decisions simultaneously.

**Solutions**:
- Single source of truth (State Manager)
- Optimistic locking for state changes
- Conflict detection and rollback
- Event sourcing for audit trail

### Performance

**Bottlenecks**:
- LLM API latency
- Vector search performance
- Database query speed

**Optimizations**:
- Batch similar operations
- Cache common queries
- Pre-generate content where possible
- Use streaming responses for narration
- Parallel agent execution when independent

## Technology Stack Recommendations

### Core Framework
- **Python**: Rich AI/ML ecosystem, good async support
- **Node.js**: Alternative for better real-time performance
- **LangChain/LlamaIndex**: Agent orchestration frameworks

### LLM Providers
- **OpenAI**: GPT-4 for DM, GPT-3.5 for NPCs
- **Anthropic Claude**: Strong reasoning and safety
- **Local models**: Llama 3, Mistral for privacy/cost

### Databases
- **PostgreSQL**: Primary relational store
- **Pinecone/Weaviate**: Vector search
- **Neo4j**: Knowledge graph (optional)

### Infrastructure
- **Docker**: Containerization
- **Redis**: Caching and pub/sub
- **Message Queue**: RabbitMQ or Redis for agent coordination

### Frontend
- **React/Next.js**: Web interface
- **Socket.io**: Real-time updates
- **Discord.py**: Bot integration

## Development Phases

### Phase 1: MVP (Minimum Viable Product)
- Single-player text interface
- DM agent only (no individual NPC agents)
- Basic memory system (simple log)
- Simple dice rolling
- Manual turn management
- One game system (e.g., D&D 5e)

### Phase 2: Core Features
- Multiple players
- Individual NPC agents
- Vector search memory
- Automated turn management
- Session summarization
- Safety tools

### Phase 3: Enhanced Experience
- Knowledge graph
- Faction system
- Campaign arc planning
- Content generation tools
- Web interface
- Multiple game systems

### Phase 4: Advanced Features
- Voice interface
- Visual content generation
- VTT integration
- Analytics and insights
- Mobile app
- Community features (share campaigns, etc.)

## Open Questions & Design Decisions

1. **Agent Autonomy vs Control**: How much should the DM agent act independently vs waiting for human approval?

2. **NPC Agent Threshold**: What level of importance triggers individual NPC agent vs DM handling?

3. **Memory Retention**: How aggressively to compress old memories? Risk losing important details.

4. **Consistency vs Creativity**: Balance between maintaining consistency and allowing interesting contradictions/surprises.

5. **Cost Management**: LLM API costs could be high for long campaigns. Need caching and local model strategies.

6. **Multi-Player Sync**: How to handle simultaneous player actions? Pure turn-based or allow interruptions?

7. **DM Override**: Should human DM be able to override any agent decision? How to implement cleanly?

8. **Rules Interpretation**: When rules are ambiguous, does DM agent decide or escalate to human?

9. **Content Rating**: How to automatically tag generated content for safety/comfort?

10. **Campaign Portability**: Can campaigns be exported/imported? Shared between groups?

## Next Steps

1. **Prototype**: Build Phase 1 MVP to test core concepts
2. **Evaluate**: Test with real play sessions, gather feedback
3. **Iterate**: Refine agent prompts and tool designs
4. **Scale**: Add features progressively based on user needs
5. **Optimize**: Improve performance and cost as usage grows
