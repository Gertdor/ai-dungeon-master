# Tools Catalog by Agent Type

## DM Agent Tools

The primary orchestrator and world manager.

### Memory & State Management
- `create_session_log` - Create new session with metadata
- `append_to_session_log` - Add event to current session log
- `query_session_history` - Search past events by keywords, participants, location, timeframe
- `create_session_summary` - Generate summary of session with title
- `create_memory_snapshot` - Create compressed memory for long-term storage
- `retrieve_memories` - Fetch relevant memories based on context
- `update_world_state` - Modify global world state (time, politics, economy, etc.)
- `query_world_state` - Get current state of world variables

### Scenario & Campaign Management
- `create_scenario_hook` - Generate scenario seed/hook
- `flesh_out_scenario` - Expand hook into detailed outline
- `create_campaign_arc` - Define overarching storyline
- `update_campaign_progress` - Mark plot beats as completed
- `generate_contingency_branch` - Create alternative paths for player choices
- `query_active_plot_threads` - List ongoing narrative threads

### NPC & Faction Management
- `create_npc` - Generate new NPC with full profile
- `update_npc` - Modify NPC attributes, knowledge, or goals
- `query_npc` - Retrieve NPC information
- `simulate_npc_conversation` - Run conversation between two NPCs
- `propagate_knowledge` - Share information between NPCs based on social network
- `create_faction` - Define organization with goals and resources
- `update_faction_state` - Modify faction standing, resources, actions
- `query_faction_relations` - Get relationship status between factions
- `generate_faction_action` - Create offscreen faction activity

### Rules & Mechanics
- `query_rulebook` - Search rules by keyword or situation
- `interpret_rule` - Get clarification on complex rule interaction
- `roll_dice` - Execute dice roll with notation and modifiers
- `create_stat_block` - Generate creature/NPC mechanical stats
- `calculate_challenge_rating` - Assess encounter difficulty

### Encounter & Content Generation
- `generate_encounter` - Create combat or challenge encounter
- `generate_loot` - Create treasure and rewards
- `generate_location` - Create location description with details
- `generate_npc_on_the_fly` - Quick NPC generation for unexpected needs
- `generate_clue` - Create investigation clue based on context

### Turn & Flow Management
- `initialize_initiative` - Start initiative tracking
- `get_next_turn` - Determine whose turn it is
- `override_turn_order` - Manually adjust turn order
- `pause_game` - Pause for OOC discussion
- `resume_game` - Resume gameplay after pause

### Player Interface
- `send_narration` - Deliver narrative description to players
- `request_player_action` - Prompt player for decision
- `offer_alternatives` - Suggest alternative actions to player
- `trigger_safety_protocol` - Handle content boundary requests
- `send_ooc_message` - Communicate out of character

### Analysis & Adaptation
- `analyze_player_engagement` - Assess player interest and energy
- `check_pacing` - Evaluate narrative pacing
- `identify_spotlight_imbalance` - Check if players are getting equal attention
- `suggest_personal_moment` - Identify opportunity for character development

## NPC Agent Tools

Individual NPCs with limited, character-appropriate knowledge.

### Memory & Knowledge
- `retrieve_personal_memory` - Access own memory and experiences
- `remember_interaction` - Store memory of conversation or event
- `query_knowledge` - Check what this NPC knows about a topic
- `update_emotional_state` - Change feelings toward PC or situation
- `share_information` - Tell another character something (DM logs this)

### Interaction
- `speak_to_pc` - Say something to player character
- `perform_action` - Describe action this NPC takes
- `react_to_event` - Generate reaction to what just happened
- `ask_question` - Ask PC or another NPC a question

### Internal Reasoning
- `evaluate_trust` - Assess whether to trust someone
- `check_motivation` - Determine if action aligns with goals
- `consider_options` - Weigh different courses of action
- `assess_danger` - Evaluate threat level of situation

### Limited Rules Access
- `roll_for_action` - Make ability check or save (initiated through DM)
- `use_ability` - Activate character ability or spell

Note: NPCs should NOT have access to:
- Global world state beyond what they'd know
- Other NPCs' thoughts or memories
- Player character thoughts or plans
- Meta-game information
- Full rulebooks (only their own stats)

## Player Character Agent Tools (Optional)

If implementing PC assistance agents to help players.

### Character Management
- `view_character_sheet` - Display character stats and abilities
- `update_character_notes` - Add personal notes
- `track_resources` - Monitor HP, spell slots, ammo, etc.
- `level_up_character` - Apply level progression

### Action Support
- `suggest_actions` - Offer action options based on abilities
- `calculate_modifiers` - Compute bonuses for roll
- `check_spell_details` - Look up spell information
- `query_ability` - Get details on class feature

### Memory Assistance
- `recall_event` - Search for past event from player's perspective
- `list_known_npcs` - Show NPCs this PC has met
- `show_active_quests` - Display ongoing objectives
- `view_relationship_status` - Show NPC relationships

## Orchestrator Agent Tools

Manages the flow between agents and ensures coherent operation.

### Agent Coordination
- `activate_agent` - Give control to specific agent (DM, NPC, PC)
- `request_agent_action` - Ask agent to perform specific action
- `synchronize_context` - Share relevant context with agent
- `merge_agent_outputs` - Combine multiple agent responses

### Context Management
- `build_context_window` - Assemble relevant information for agent
- `prioritize_memories` - Rank memories by relevance
- `compress_history` - Summarize long context for token efficiency
- `manage_information_access` - Filter what each agent can see

### Flow Control
- `determine_next_speaker` - Decide which agent acts next
- `handle_interruption` - Process turn override or OOC request
- `resolve_conflict` - Handle contradictory agent outputs
- `maintain_turn_queue` - Manage action order

### Monitoring
- `check_consistency` - Verify world state coherence
- `detect_deadlock` - Identify when game is stalled
- `monitor_token_usage` - Track computational costs
- `log_agent_interactions` - Record agent communication for debugging

## Utility Tools (Shared)

Available to multiple agent types with appropriate permissions.

### Text Generation
- `generate_description` - Create atmospheric description
- `generate_dialogue` - Create character-appropriate speech
- `generate_name` - Create appropriate name for person/place/thing
- `rephrase_text` - Rewrite text in different tone or style

### Lookup & Reference
- `search_bestiary` - Find monster by name or type
- `search_items` - Look up equipment or magic items
- `search_spells` - Find spell by name, level, or effect
- `search_conditions` - Look up status effects and rules

### Randomization
- `roll_on_table` - Use random table from rulebook
- `generate_random_npc` - Quick NPC with random traits
- `select_random_encounter` - Choose encounter from list
- `shuffle_list` - Randomize order of items

### Computation
- `calculate_distance` - Compute movement and ranges
- `calculate_damage` - Sum damage dice and modifiers
- `check_line_of_sight` - Determine if target is visible
- `calculate_travel_time` - Determine journey duration

## Tool Access Matrix

| Tool Category | DM | NPC | PC | Orchestrator |
|---------------|----|----|----|--------------|
| Memory Management | Full | Personal Only | Personal Only | Full |
| World State | Full | Limited | Limited | Read Only |
| NPC Creation | Full | No | No | No |
| Rules Access | Full | Limited | Full | Read Only |
| Dice Rolling | Full | Through DM | Full | No |
| Turn Management | Full | No | Request Only | Full |
| Player Communication | Full | Yes | Yes | No |
| Other Agent Memory | Full | No | No | Full |
| Context Building | Yes | No | No | Full |

## Implementation Notes

### Tool Design Principles
1. **Scoped Access**: Each agent only gets tools appropriate to their role
2. **Auditable**: All tool calls should be logged for consistency checking
3. **Reversible**: State-changing tools should support undo/rollback
4. **Idempotent**: Where possible, repeated tool calls should be safe
5. **Fast**: Frequently used tools should be optimized for speed
6. **Clear Errors**: Tool failures should provide actionable error messages

### Tool Call Patterns
- **Query then Act**: Read current state before modifying
- **Validate Input**: Check parameters before executing
- **Confirm Major Changes**: Require DM confirmation for significant world alterations
- **Batch Updates**: Group related changes for efficiency
- **Progressive Disclosure**: Return summaries first, details on request

### Security Considerations
- NPCs cannot read other NPCs' thoughts or memories directly
- Players cannot modify world state without DM approval
- All tool calls are logged and can be audited
- Sensitive information (player plans, DM notes) is access-controlled
- Tool permissions can be dynamically adjusted by DM
