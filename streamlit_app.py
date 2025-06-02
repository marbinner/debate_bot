"""
🎯 Debate Bot - AI-Powered Debate Platform

A Streamlit application that enables debates between humans and AI bots, or between two AI bots
with different personalities. Built with Google's Gemini API for natural language generation.

Features:
- Human vs Bot debates with customizable AI personalities
- Bot vs Bot debates with automated multi-turn generation
- Real-time streaming responses with thinking process visibility
- Configurable response creativity (temperature)
- Save/load conversation states
- Export debates to Markdown
- Multiple debate personalities (debate_bro, debate_sis, etc.)
- Progress tracking for multi-turn generations

Architecture:
- Frontend: Streamlit with custom CSS for responsive design
- Backend: ChatBot and BotDebateManager classes (from chatbot.py)
- AI Model: Google Gemini via API
- State Management: Streamlit session state with proper cleanup
- Configuration: JSON-based personality system

Usage:
1. Set GOOGLE_API_KEY in .env file
2. Configure personalities in personalities.json
3. Run: streamlit run streamlit_app.py
4. Choose Human vs Bot or Bot vs Bot mode
5. Start debating!

Author: AI Assistant
Version: 2.0
"""

import streamlit as st
import asyncio
import os
import json
from typing import Optional, Dict, Tuple
from chatbot import ChatBot, BotDebateManager
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def load_prompt_from_file(prompt_file: str) -> str:
    """Load system prompt from an external file."""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        st.error(f"❌ Prompt file not found: {prompt_file}")
        return ""
    except Exception as e:
        st.error(f"❌ Error reading prompt file {prompt_file}: {e}")
        return ""

def load_personalities() -> Dict:
    """Load personality configurations from JSON file."""
    try:
        with open('personalities.json', 'r') as f:
            personalities = json.load(f)
        
        # Process each personality to load external prompt files if needed
        for key, personality in personalities.items():
            if 'prompt_file' in personality:
                # Load prompt from external file
                prompt_content = load_prompt_from_file(personality['prompt_file'])
                personality['system_prompt'] = prompt_content
            elif 'system_prompt' not in personality:
                # Fallback if neither prompt_file nor system_prompt is provided
                personality['system_prompt'] = "You are a helpful AI assistant."
        
        return personalities
    except FileNotFoundError:
        st.error("❌ personalities.json file not found")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Error reading personalities.json file")
        return {}

# Configure Streamlit page
st.set_page_config(
    page_title="🎯 Debate Bot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile/narrow screen experience
st.markdown("""
<style>
    /* Reduce padding on narrow screens */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Make chat messages use full width on small screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Ensure chat input uses full width */
        .stChatInput > div {
            max-width: none !important;
        }
    }
    
    /* Improve sidebar width on narrow screens */
    @media (max-width: 1024px) {
        .css-1d391kg {
            width: 280px;
        }
    }
    
    /* Better chat message spacing */
    .stChatMessage {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """
    Initialize all session state variables on first run.
    
    This function sets up the application state including:
    - Chat/debate history tracking
    - Bot configuration and status
    - UI state management
    - Mode selection (human vs bot / bot vs bot)
    - Generation progress tracking
    
    Called automatically on app startup and handles both human vs bot
    and bot vs bot mode initialization.
    """
    if 'bot' not in st.session_state:
        st.session_state.bot = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'thoughts' not in st.session_state:
        st.session_state.thoughts = []
    if 'message_personalities' not in st.session_state:
        st.session_state.message_personalities = []  # Track which personality generated each message
    if 'show_thoughts' not in st.session_state:
        st.session_state.show_thoughts = True
    if 'bot_initialized' not in st.session_state:
        st.session_state.bot_initialized = False
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    if 'current_personality' not in st.session_state:
        st.session_state.current_personality = "debate_bro"
    if 'personalities' not in st.session_state:
        st.session_state.personalities = load_personalities()
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 1.0
    if 'state_loaded' not in st.session_state:
        st.session_state.state_loaded = False
    
    # Bot vs Bot debate mode variables
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = "human_vs_bot"  # or "bot_vs_bot"
    if 'debate_manager' not in st.session_state:
        st.session_state.debate_manager = None
    if 'debate_initialized' not in st.session_state:
        st.session_state.debate_initialized = False
    if 'debate_history' not in st.session_state:
        st.session_state.debate_history = []
    if 'debate_personality_a' not in st.session_state:
        st.session_state.debate_personality_a = "debate_bro"
    if 'debate_personality_b' not in st.session_state:
        st.session_state.debate_personality_b = "debate_bro_v2"
    if 'debate_temperature_a' not in st.session_state:
        st.session_state.debate_temperature_a = 1.0
    if 'debate_temperature_b' not in st.session_state:
        st.session_state.debate_temperature_b = 1.0
    if 'debate_generating' not in st.session_state:
        st.session_state.debate_generating = False
    if 'initial_claim' not in st.session_state:
        st.session_state.initial_claim = ""
    if 'auto_respond_next' not in st.session_state:
        st.session_state.auto_respond_next = False
    if 'turns_per_button' not in st.session_state:
        st.session_state.turns_per_button = 2
    if 'turns_remaining' not in st.session_state:
        st.session_state.turns_remaining = 0
    if 'turns_completed' not in st.session_state:
        st.session_state.turns_completed = 0
    
    # Auto-initialize the bot after personalities are loaded
    if not st.session_state.bot_initialized and st.session_state.personalities:
        initialize_bot()

def initialize_bot() -> bool:
    """Set up the ChatBot with API key and current personality."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Please set GOOGLE_API_KEY environment variable in your .env file")
            st.info("Create a .env file with: GOOGLE_API_KEY=your_api_key_here")
            return False
        
        # Get current personality system prompt
        personalities = st.session_state.personalities
        if st.session_state.current_personality in personalities:
            system_prompt = personalities[st.session_state.current_personality]["system_prompt"]
        else:
            system_prompt = "You are a helpful AI assistant."
        
        # Initialize bot with personality and temperature
        st.session_state.bot = ChatBot(api_key, temperature=st.session_state.temperature)
        st.session_state.bot.update_system_prompt(system_prompt)
        st.session_state.bot_initialized = True
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize bot: {e}")
        return False

def update_personality(new_personality: str):
    """Switch to a different personality and update the bot's system prompt."""
    if st.session_state.bot and new_personality in st.session_state.personalities:
        system_prompt = st.session_state.personalities[new_personality]["system_prompt"]
        st.session_state.bot.update_system_prompt(system_prompt)
        st.session_state.current_personality = new_personality

def update_temperature(new_temperature: float):
    """Update the bot's temperature setting."""
    if st.session_state.bot:
        st.session_state.bot.update_temperature(new_temperature)
        st.session_state.temperature = new_temperature

async def get_bot_response_stream(user_message: str, include_thoughts: bool = True):
    """Stream bot response with optional thinking process."""
    if st.session_state.bot is None:
        yield "Bot not initialized", False
        return
    
    try:
        async for content, is_thought in st.session_state.bot.generate_response_stream(
            user_message, include_thoughts=include_thoughts
        ):
            yield content, is_thought
    except Exception as e:
        yield f"Error: {str(e)}", False

def display_message(role: str, content: str, thought: Optional[str] = None, personality_key: Optional[str] = None, message_index: Optional[int] = None):
    """Display a single message (user or bot) in the chat interface."""
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        # Get personality info for bot avatar and name
        personalities = st.session_state.personalities
        if personality_key and personality_key in personalities:
            personality = personalities[personality_key]
            avatar = personality["emoji"]
            personality_name = personality["name"]
        else:
            # Fallback to current personality
            current_personality = personalities.get(st.session_state.current_personality, {})
            avatar = current_personality.get("emoji", "🤖")
            personality_name = current_personality.get("name", "Bot")
        
        with st.chat_message("assistant", avatar=avatar):
            # Show which personality responded
            if personality_key and personality_key in personalities:
                st.caption(f"*{personality_name}*")
            
            # Show thinking process if available and enabled
            if thought and thought.strip() and st.session_state.show_thoughts:
                with st.expander("💭 Bot's Thinking", expanded=False):
                    st.write(thought)
            
            # Show the actual response
            st.write(content)

def export_chat_to_markdown() -> str:
    """Export chat history to markdown format, excluding internal thinking."""
    import datetime
    
    # Start with header
    markdown_content = []
    markdown_content.append("# Debate Bot Chat History")
    markdown_content.append(f"*Exported on {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
    markdown_content.append("")
    
    # If no messages, return empty chat message
    if not st.session_state.messages:
        markdown_content.append("*No messages in this conversation.*")
        return "\n".join(markdown_content)
    
    # Process each message
    for i, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            markdown_content.append("## 👤 You")
            markdown_content.append(content)
        else:  # assistant
            # Get personality info for this message
            personality_key = st.session_state.message_personalities[i] if i < len(st.session_state.message_personalities) else None
            personalities = st.session_state.personalities
            
            if personality_key and personality_key in personalities:
                personality = personalities[personality_key]
                emoji = personality["emoji"]
                name = personality["name"]
            else:
                # Fallback to current personality
                current_personality = personalities.get(st.session_state.current_personality, {})
                emoji = current_personality.get("emoji", "🤖")
                name = current_personality.get("name", "Bot")
            
            markdown_content.append(f"## {emoji} {name}")
            markdown_content.append(content)
        
        markdown_content.append("")  # Add blank line between messages
    
    return "\n".join(markdown_content)

def export_full_state() -> str:
    """Export complete conversation state as JSON for later loading."""
    import datetime
    
    state = {
        "version": "1.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "current_personality": st.session_state.current_personality,
        "temperature": st.session_state.temperature,
        "show_thoughts": st.session_state.show_thoughts,
        "messages": st.session_state.messages,
        "thoughts": st.session_state.thoughts,
        "message_personalities": st.session_state.message_personalities,
        "metadata": {
            "exported_from": "streamlit_app",
            "message_count": len(st.session_state.messages),
            "user_messages": len([msg for msg in st.session_state.messages if msg["role"] == "user"]),
            "assistant_messages": len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
        }
    }
    
    return json.dumps(state, indent=2, ensure_ascii=False)

def load_full_state(state_data: str) -> Tuple[bool, str]:
    """
    Load complete conversation state from JSON data.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        state = json.loads(state_data)
        
        # Validate state format
        required_fields = ["messages", "thoughts", "message_personalities", "current_personality"]
        for field in required_fields:
            if field not in state:
                return False, f"Invalid state file: missing field '{field}'"
        
        # Validate that the loaded personality exists in the current system
        personalities = st.session_state.personalities
        if state["current_personality"] not in personalities:
            # Fall back to default personality if loaded personality doesn't exist
            if "debate_bro" in personalities:
                fallback_personality = "debate_bro"
            else:
                fallback_personality = list(personalities.keys())[0] if personalities else "debate_bro"
            
            state["current_personality"] = fallback_personality
        
        # Validate array lengths to prevent index errors
        messages = state["messages"]
        thoughts = state["thoughts"]
        message_personalities = state["message_personalities"]
        
        # Ensure all arrays have the same length
        max_length = len(messages)
        
        # Extend thoughts array if needed
        while len(thoughts) < max_length:
            thoughts.append(None)
        
        # Extend message_personalities array if needed  
        while len(message_personalities) < max_length:
            message_personalities.append(None)
        
        # Truncate if arrays are too long
        thoughts = thoughts[:max_length]
        message_personalities = message_personalities[:max_length]
        
        # Load state into session
        st.session_state.messages = messages
        st.session_state.thoughts = thoughts
        st.session_state.message_personalities = message_personalities
        st.session_state.current_personality = state["current_personality"]
        st.session_state.state_loaded = True
        
        # Load optional settings with defaults
        if "temperature" in state:
            st.session_state.temperature = state["temperature"]
        if "show_thoughts" in state:
            st.session_state.show_thoughts = state["show_thoughts"]
        
        # Update bot with loaded settings if bot is initialized
        if st.session_state.bot:
            try:
                # Update bot's conversation history
                bot_history = []
                for msg in st.session_state.messages:
                    bot_history.append({"role": msg["role"], "content": msg["content"]})
                st.session_state.bot.conversation_history = bot_history
                
                # Update bot's system prompt based on current personality
                if st.session_state.current_personality in personalities:
                    system_prompt = personalities[st.session_state.current_personality]["system_prompt"]
                    st.session_state.bot.update_system_prompt(system_prompt)
                
                # Update bot's temperature
                st.session_state.bot.update_temperature(st.session_state.temperature)
            except Exception as e:
                return False, f"Error updating bot state: {str(e)}"
        
        message_count = len(st.session_state.messages)
        metadata = state.get("metadata", {})
        
        return True, f"Successfully loaded {message_count} messages from {metadata.get('timestamp', 'unknown time')}"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return False, f"Error loading state: {str(e)}"

def clear_conversation():
    """Clear all conversation data and reset to initial state."""
    st.session_state.messages = []
    st.session_state.thoughts = []
    st.session_state.message_personalities = []
    st.session_state.state_loaded = False
    
    # Clear file tracking to allow reloading
    st.session_state.pop("last_loaded_file", None)
    
    # Clear bot's history if bot is initialized
    if st.session_state.bot:
        st.session_state.bot.clear_history()

def initialize_debate_manager() -> bool:
    """Initialize the debate manager with API key."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Please set GOOGLE_API_KEY environment variable in your .env file")
            return False
        
        st.session_state.debate_manager = BotDebateManager(api_key)
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize debate manager: {e}")
        return False

def setup_debate_bots() -> bool:
    """Set up the debate with selected personalities and temperatures."""
    if not st.session_state.debate_manager:
        if not initialize_debate_manager():
            return False
    
    personalities = st.session_state.personalities
    
    # Get personality prompts
    personality_a = personalities.get(st.session_state.debate_personality_a, {})
    personality_b = personalities.get(st.session_state.debate_personality_b, {})
    
    if not personality_a.get("system_prompt") or not personality_b.get("system_prompt"):
        st.error("❌ Selected personalities do not have valid system prompts")
        return False
    
    try:
        success = st.session_state.debate_manager.setup_debate(
            st.session_state.debate_personality_a,
            personality_a["system_prompt"],
            st.session_state.debate_personality_b,
            personality_b["system_prompt"],
            st.session_state.debate_temperature_a,
            st.session_state.debate_temperature_b
        )
        
        if success:
            st.session_state.debate_initialized = True
            return True
        else:
            st.error("❌ Failed to set up debate bots")
            return False
            
    except Exception as e:
        st.error(f"❌ Error setting up debate: {e}")
        return False

def start_new_debate(initial_claim: str, starting_bot: str = "A") -> bool:
    """Start a new debate with the given initial claim."""
    if not st.session_state.debate_initialized:
        if not setup_debate_bots():
            return False
    
    try:
        st.session_state.debate_manager.start_debate(initial_claim, starting_bot)
        st.session_state.debate_history = st.session_state.debate_manager.get_debate_history()
        return True
    except Exception as e:
        st.error(f"❌ Error starting debate: {e}")
        return False

def clear_debate():
    """Clear the current debate."""
    st.session_state.debate_history = []
    st.session_state.initial_claim = ""
    if st.session_state.debate_manager:
        st.session_state.debate_manager.clear_debate()

async def get_next_debate_turn():
    """Generate the next turn in the debate."""
    if not st.session_state.debate_manager:
        return
    
    try:
        async for content, is_thought, bot_key in st.session_state.debate_manager.next_turn_stream(
            include_thoughts=st.session_state.show_thoughts
        ):
            yield content, is_thought, bot_key
        
        # Update session state with new history
        st.session_state.debate_history = st.session_state.debate_manager.get_debate_history()
        
    except Exception as e:
        yield f"Error generating next turn: {str(e)}", False, "Error"

def display_debate_message(message: Dict, personalities: Dict):
    """Display a single debate message."""
    bot_key = message["bot"]
    content = message["content"]
    thought = message.get("thought")
    turn = message.get("turn", 0)
    personality_key = message.get("personality", "")
    
    # Get personality info
    if personality_key in personalities:
        personality = personalities[personality_key]
        base_avatar = personality["emoji"]
        personality_name = personality["name"]
    else:
        base_avatar = "🤖"
        personality_name = "Bot"
    
    # Always distinguish between Bot A and Bot B with different colored indicators
    if bot_key == "A":
        avatar = "🔵"  # Blue circle for Bot A
        name = f"Bot A ({personality_name}) {base_avatar}"
    else:  # bot_key == "B"
        avatar = "🔴"  # Red circle for Bot B  
        name = f"Bot B ({personality_name}) {base_avatar}"
    
    with st.chat_message("assistant", avatar=avatar):
        st.caption(f"*Turn {turn + 1}: {name}*")
        
        # Show thinking process if available and enabled (collapsed by default)
        if thought and thought.strip() and st.session_state.show_thoughts:
            with st.expander(f"💭 {name}'s Thinking", expanded=False):
                st.write(thought)
        
        # Show the actual response
        st.write(content)

def export_debate_to_markdown() -> str:
    """Export debate history to markdown format."""
    if not st.session_state.debate_manager:
        return "No debate in progress."
    
    return st.session_state.debate_manager.export_debate_to_markdown(st.session_state.personalities)

def export_debate_state() -> str:
    """Export complete debate state as JSON."""
    import datetime
    
    if not st.session_state.debate_manager:
        return "{}"
    
    state = {
        "version": "1.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "mode": "bot_vs_bot",
        "debate_personality_a": st.session_state.debate_personality_a,
        "debate_personality_b": st.session_state.debate_personality_b,
        "debate_temperature_a": st.session_state.debate_temperature_a,
        "debate_temperature_b": st.session_state.debate_temperature_b,
        "show_thoughts": st.session_state.show_thoughts,
        "debate_history": st.session_state.debate_history,
        "initial_claim": st.session_state.initial_claim,
        "metadata": {
            "exported_from": "streamlit_app_debate_mode",
            "total_turns": len(st.session_state.debate_history),
            "current_turn": st.session_state.debate_manager.current_turn if st.session_state.debate_manager else "Unknown"
        }
    }
    
    return json.dumps(state, indent=2, ensure_ascii=False)

def main():
    """
    Main application entry point.
    
    Handles the top-level UI structure including:
    - Mode selection in sidebar (Human vs Bot / Bot vs Bot)
    - Conditional sidebar content based on selected mode
    - Routing to appropriate interface functions
    - State initialization and management
    
    The app uses a sidebar-driven architecture where the mode selector
    determines which sidebar controls and main interface to display.
    """
    initialize_session_state()
    
    # === SIDEBAR WITH MODE SELECTOR ===
    with st.sidebar:
        st.title("🎯 Debate Bot")
        
        # Mode selector at the top of sidebar
        current_mode_index = 0 if st.session_state.app_mode == "human_vs_bot" else 1
        app_mode = st.radio(
            "Select Mode:",
            options=["👤 Human vs Bot", "🤖 Bot vs Bot"],
            index=current_mode_index,
            horizontal=False
        )
        
        # Update session state based on selection and trigger rerun if changed
        new_mode = "human_vs_bot" if app_mode == "👤 Human vs Bot" else "bot_vs_bot"
        if new_mode != st.session_state.app_mode:
            st.session_state.app_mode = new_mode
            st.rerun()
        
        st.divider()
        
        # Show appropriate sidebar content based on mode
        if st.session_state.app_mode == "human_vs_bot":
            human_vs_bot_sidebar()
        else:
            bot_vs_bot_sidebar()
    
    # === MAIN CONTENT ===
    if st.session_state.app_mode == "human_vs_bot":
        human_vs_bot_interface()
    else:
        bot_vs_bot_interface()

def human_vs_bot_sidebar():
    """Sidebar content for human vs bot mode."""
    st.header("⚙️ Bot Settings")
    
    # Bot status indicator
    if st.session_state.bot_initialized:
        st.success("✅ Bot Ready")
    else:
        st.error("❌ Bot Not Ready")
    
    st.divider()
    
    # Personality selector
    personalities = st.session_state.personalities
    if personalities:
        st.subheader("🎭 Personality")
        
        # Get current personality for display
        current_personality_key = st.session_state.current_personality
        current_personality = personalities.get(current_personality_key, {})
        
        # Create dropdown options with emoji + name
        personality_options = {}
        for key, personality in personalities.items():
            display_name = f"{personality['emoji']} {personality['name']}"
            personality_options[display_name] = key
        
        # Handle case where current personality doesn't exist
        current_display_name = f"{current_personality.get('emoji', '🎯')} {current_personality.get('name', 'Debate Bot')}"
        
        try:
            current_index = list(personality_options.keys()).index(current_display_name)
        except ValueError:
            current_index = 0
            # Reset to first available personality if current one is invalid
            if personality_options:
                first_key = list(personality_options.values())[0]
                st.session_state.current_personality = first_key
        
        # Personality dropdown (disabled during generation)
        selected_display = st.selectbox(
            "Choose personality:",
            options=list(personality_options.keys()),
            index=current_index,
            disabled=st.session_state.generating,
            key="personality_selector"
        )
        
        selected_personality_key = personality_options[selected_display]
        
        # Show personality description
        if selected_personality_key in personalities:
            st.info(personalities[selected_personality_key]["description"])
        
        # Update personality if changed (not during generation)
        if selected_personality_key != st.session_state.current_personality and not st.session_state.generating:
            try:
                update_personality(selected_personality_key)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update personality: {e}")
    else:
        st.warning("⚠️ No personalities available. Check personalities.json file.")
    
    st.divider()
    
    # Temperature control
    st.subheader("🌡️ Temperature")
    temperature_value = st.slider(
        "Response creativity/randomness:",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        step=0.1,
        help="Lower values (0.0-0.3) = more focused and deterministic responses. Higher values (0.8-2.0) = more creative and varied responses.",
        disabled=st.session_state.generating
    )
    
    # Update temperature if changed (not during generation)
    if abs(temperature_value - st.session_state.temperature) > 0.01 and not st.session_state.generating:
        try:
            update_temperature(temperature_value)
        except Exception as e:
            st.error(f"Failed to update temperature: {e}")
    
    st.divider()
    
    # Generation status
    if st.session_state.generating:
        st.info("🔄 Generating response...")
    
    # Thinking toggle
    show_thoughts_changed = st.checkbox(
        "💭 Show Bot's Thinking", 
        value=st.session_state.show_thoughts,
        help="Display the bot's internal thinking process",
        disabled=st.session_state.generating
    )
    
    # Handle thinking toggle change (not during generation)
    if show_thoughts_changed != st.session_state.show_thoughts and not st.session_state.generating:
        st.session_state.show_thoughts = show_thoughts_changed
        st.rerun()  # Rerun to update all message displays
    
    st.divider()
    
    # Save/Load & Export section
    st.subheader("💾 Save & Load")
    
    # Only show save/load options if not currently generating
    if not st.session_state.generating:
        # Clear conversation button
        if st.session_state.messages:
            if st.button("🗑️ Clear Conversation", type="secondary", use_container_width=True):
                clear_conversation()
                st.rerun()
        
        # Save current state section
        if st.session_state.messages:
            st.write("**Save Current Conversation:**")
            
            # Generate filenames with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Full state save (JSON)
            state_data = export_full_state()
            state_filename = f"debate_state_{timestamp}.json"
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 Save State",
                    data=state_data,
                    file_name=state_filename,
                    mime="application/json",
                    help="Save complete conversation state (can be loaded later to continue)",
                    use_container_width=True
                )
            
            with col2:
                # Markdown export
                markdown_content = export_chat_to_markdown()
                markdown_filename = f"debate_chat_{timestamp}.md"
                
                st.download_button(
                    label="📄 Export MD",
                    data=markdown_content,
                    file_name=markdown_filename,
                    mime="text/markdown",
                    help="Export as readable markdown (no state info)",
                    use_container_width=True
                )
        
        # Load state section
        st.write("**Load Previous Conversation:**")
        
        uploaded_file = st.file_uploader(
            "Choose a conversation state file",
            type=['json'],
            help="Upload a .json state file to continue a previous conversation",
            key="human_state_uploader"
        )
        
        if uploaded_file is not None:
            # Check if we've already processed this file to prevent re-processing
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("last_loaded_file") == file_id:
                st.info("💡 File already loaded. Clear conversation or upload a different file to load again.")
            else:
                with st.spinner("Loading conversation state..."):
                    try:
                        # Read the uploaded file
                        state_data = uploaded_file.read().decode('utf-8')
                        
                        # Load the state
                        success, message = load_full_state(state_data)
                        
                        if success:
                            st.success(f"✅ {message}")
                            # Mark this file as processed
                            st.session_state.last_loaded_file = file_id
                            
                            # Force reinitialize personality and temperature in bot
                            if st.session_state.bot_initialized:
                                try:
                                    update_personality(st.session_state.current_personality)
                                    update_temperature(st.session_state.temperature)
                                    st.info("🔄 Bot updated with loaded settings")
                                except Exception as e:
                                    st.warning(f"⚠️ Note: {str(e)}")
                            
                            # Add a small delay before rerun to ensure state is stable
                            time.sleep(0.1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
        
        # Show current conversation info
        if st.session_state.messages:
            with st.expander("📊 Current Conversation Info", expanded=False):
                user_msgs = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
                bot_msgs = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
                
                st.text(f"Total Messages: {len(st.session_state.messages)}")
                st.text(f"Your Messages: {user_msgs}")
                st.text(f"Bot Messages: {bot_msgs}")
                st.text(f"Current Personality: {st.session_state.personalities.get(st.session_state.current_personality, {}).get('name', 'Unknown')}")
                st.text(f"Temperature: {st.session_state.temperature}")
                st.text(f"Show Thoughts: {st.session_state.show_thoughts}")
    else:
        st.info("⏳ Save/Load available after response")

def bot_vs_bot_sidebar():
    """Sidebar content for bot vs bot mode."""
    st.header("⚙️ Bot vs Bot Setup")
    
    personalities = st.session_state.personalities
    if not personalities:
        st.error("❌ No personalities available. Check personalities.json file.")
        return
    
    # Create personality options
    personality_options = {}
    for key, personality in personalities.items():
        display_name = f"{personality['emoji']} {personality['name']}"
        personality_options[display_name] = key
    
    # Compact bot configuration in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔵 Bot A**")
        # Get current index for Bot A
        current_a_display = None
        for display, key in personality_options.items():
            if key == st.session_state.debate_personality_a:
                current_a_display = display
                break
        
        if current_a_display is None:
            current_a_display = list(personality_options.keys())[0]
            st.session_state.debate_personality_a = personality_options[current_a_display]
        
        selected_a_display = st.selectbox(
            "Personality:",
            options=list(personality_options.keys()),
            index=list(personality_options.keys()).index(current_a_display),
            disabled=st.session_state.debate_generating,
            key="bot_a_personality_select"
        )
        
        # Update state if changed
        new_personality_a = personality_options[selected_a_display]
        if new_personality_a != st.session_state.debate_personality_a:
            st.session_state.debate_personality_a = new_personality_a
        
        # Bot A temperature
        st.session_state.debate_temperature_a = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.debate_temperature_a,
            step=0.1,
            disabled=st.session_state.debate_generating,
            key="bot_a_temp"
        )
    
    with col2:
        st.write("**🔴 Bot B**")
        # Get current index for Bot B
        current_b_display = None
        for display, key in personality_options.items():
            if key == st.session_state.debate_personality_b:
                current_b_display = display
                break
        
        if current_b_display is None and len(personality_options) > 1:
            current_b_display = list(personality_options.keys())[1]
            st.session_state.debate_personality_b = personality_options[current_b_display]
        elif current_b_display is None:
            current_b_display = list(personality_options.keys())[0]
            st.session_state.debate_personality_b = personality_options[current_b_display]
        
        selected_b_display = st.selectbox(
            "Personality:",
            options=list(personality_options.keys()),
            index=list(personality_options.keys()).index(current_b_display),
            disabled=st.session_state.debate_generating,
            key="bot_b_personality_select"
        )
        
        # Update state if changed
        new_personality_b = personality_options[selected_b_display]
        if new_personality_b != st.session_state.debate_personality_b:
            st.session_state.debate_personality_b = new_personality_b
        
        # Bot B temperature
        st.session_state.debate_temperature_b = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.debate_temperature_b,
            step=0.1,
            disabled=st.session_state.debate_generating,
            key="bot_b_temp"
        )
    
    st.divider()
    
    # Compact controls section
    col1, col2 = st.columns(2)
    
    with col1:
        # Thinking toggle
        show_thoughts_changed = st.checkbox(
            "💭 Show Thinking", 
            value=st.session_state.show_thoughts,
            disabled=st.session_state.debate_generating
        )
        
        if show_thoughts_changed != st.session_state.show_thoughts and not st.session_state.debate_generating:
            st.session_state.show_thoughts = show_thoughts_changed
            st.rerun()
    
    with col2:
        # Generation status
        if st.session_state.debate_generating:
            st.info("🔄 Generating...")
        elif st.session_state.debate_history:
            st.success("✅ Ready")
        else:
            st.info("⏳ Setup needed")
    
    st.divider()
    
    # Turns per button press setting
    st.subheader("🔄 Generation Settings")
    turns_per_button = st.slider(
        "Turns per button press:",
        min_value=1,
        max_value=10,
        value=st.session_state.turns_per_button,
        step=1,
        help="How many back-and-forth turns to generate when you click 'Continue Debate'",
        disabled=st.session_state.debate_generating
    )
    
    # Update session state if changed
    if turns_per_button != st.session_state.turns_per_button and not st.session_state.debate_generating:
        st.session_state.turns_per_button = turns_per_button
    
    # Show progress bar during multi-turn generation
    if st.session_state.debate_generating and hasattr(st.session_state, 'turns_remaining') and hasattr(st.session_state, 'turns_completed'):
        total_turns = st.session_state.turns_per_button
        completed = getattr(st.session_state, 'turns_completed', 0)
        
        if total_turns > 1:  # Only show progress for multi-turn generation
            st.divider()
            st.subheader("📊 Generation Progress")
            
            progress_value = completed / total_turns if total_turns > 0 else 0
            st.progress(progress_value, text=f"Turn {completed} of {total_turns}")
            
            if completed > 0:
                st.caption(f"✅ {completed} completed • 🔄 {total_turns - completed} remaining")
    
    # Action buttons row
    if not st.session_state.debate_generating:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.debate_history:
                if st.button("🗑️ Clear", type="secondary", use_container_width=True):
                    clear_debate()
                    st.rerun()
        
        with col2:
            # Export dropdown
            if st.session_state.debate_history:
                with st.popover("💾 Export", use_container_width=True):
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Debate state export
                    debate_state = export_debate_state()
                    state_filename = f"debate_state_{timestamp}.json"
                    
                    st.download_button(
                        label="📄 Save State (.json)",
                        data=debate_state,
                        file_name=state_filename,
                        mime="application/json",
                        use_container_width=True
                    )
                    
                    # Markdown export
                    markdown_content = export_debate_to_markdown()
                    markdown_filename = f"bot_debate_{timestamp}.md"
                    
                    st.download_button(
                        label="📝 Export Chat (.md)",
                        data=markdown_content,
                        file_name=markdown_filename,
                        mime="text/markdown",
                        use_container_width=True
                    )
    
    # Compact debate info
    if st.session_state.debate_history and st.session_state.debate_manager:
        st.divider()
        summary = st.session_state.debate_manager.get_debate_summary()
        st.caption(f"**Turns:** {summary['total_turns']} | **Next:** Bot {summary['current_turn']}")

def human_vs_bot_interface():
    """Interface for human vs bot debates."""
    # === MAIN CHAT INTERFACE ===
    if not st.session_state.bot_initialized:
        st.info("⚠️ Bot initialization failed. Please check your API key configuration.")
        return
    
    # Display chat history (but not the currently generating message)
    for i, message in enumerate(st.session_state.messages):
        # Skip the last message if it's a user message and we're currently generating
        if (st.session_state.generating and 
            i == len(st.session_state.messages) - 1 and 
            message["role"] == "user"):
            continue
            
        thought = st.session_state.thoughts[i] if i < len(st.session_state.thoughts) else None
        personality_key = st.session_state.message_personalities[i] if i < len(st.session_state.message_personalities) else None
        display_message(message["role"], message["content"], thought, personality_key, i)
    
    # Handle user input and generation
    if st.session_state.generating and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Show the user message that triggered generation
        last_message = st.session_state.messages[-1]
        with st.chat_message("user", avatar="👤"):
            st.write(last_message["content"])
        
        # Generate bot response
        generate_bot_response()
        
        # Show disabled placeholder during generation
        st.chat_input("🔄 Bot is responding...", disabled=True, key="generating_input")
    else:
        # Chat input when not generating
        if prompt := st.chat_input("Enter your debate topic or argument...", key="active_input"):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.thoughts.append(None)
            st.session_state.message_personalities.append(None)
            st.session_state.generating = True
            st.rerun()  # Rerun to show user message and start generation

def generate_bot_response():
    """Handle bot response generation with real-time streaming."""
    prompt = st.session_state.messages[-1]["content"]
    
    # Get current personality for avatar and name
    current_personality = st.session_state.personalities.get(st.session_state.current_personality, {})
    current_avatar = current_personality.get("emoji", "🤖")
    current_name = current_personality.get("name", "Bot")
    
    # Display bot response with streaming - use full width
    with st.chat_message("assistant", avatar=current_avatar):
        st.caption(f"*{current_name}*")
        
        # Create placeholders in correct order: thoughts first, then response
        thoughts_placeholder = st.empty()
        response_placeholder = st.empty()
        
        full_response = ""
        all_thoughts = ""
        
        # Show initial state
        if st.session_state.show_thoughts:
            with thoughts_placeholder.container():
                with st.expander("💭 Bot's Thinking", expanded=False):
                    st.write("*Thinking...*")
        else:
            # Only show generating message when thinking is not displayed
            response_placeholder.write("*Generating response...*")
        
        # Stream the response in real-time
        try:
            async def stream_and_update():
                nonlocal full_response, all_thoughts
                async for content, is_thought in get_bot_response_stream(prompt, include_thoughts=True):
                    if is_thought:
                        # Update thinking content
                        all_thoughts += content
                        if st.session_state.show_thoughts:
                            with thoughts_placeholder.container():
                                with st.expander("💭 Bot's Thinking", expanded=False):
                                    st.write(all_thoughts)
                    else:
                        # Update response content
                        full_response += content
                        if full_response.strip():
                            response_placeholder.write(full_response)
            
            # Run the streaming
            asyncio.run(stream_and_update())
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            response_placeholder.write(error_msg)
            full_response = error_msg
    
    # Save completed response to session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.thoughts.append(all_thoughts.strip() if all_thoughts.strip() else None)
    st.session_state.message_personalities.append(st.session_state.current_personality)
    st.session_state.generating = False
    
    # Rerun to re-enable chat input and sidebar controls
    st.rerun()

def bot_vs_bot_interface():
    """
    Main interface for Bot vs Bot debate mode.
    
    Provides a two-phase interface:
    1. Setup Phase: Initial claim input, bot selection, start button
    2. Debate Phase: Chat history display, progress tracking, continue controls
    
    Features:
    - Real-time text input with immediate button state updates
    - Automatic initial response generation (2 turns on start)
    - Configurable multi-turn generation via continue button
    - Progress tracking in sidebar during generation
    - Clean state transitions between setup and debate phases
    
    The interface uses conditional rendering to hide setup UI immediately
    when generation starts, providing smooth user experience.
    """
    # Get personalities for consistent access throughout function
    personalities = st.session_state.personalities
    
    # === MAIN DEBATE INTERFACE ===
    if not st.session_state.debate_history and not st.session_state.debate_generating:
        # Setup Phase: Show debate configuration interface
        st.subheader("🎯 Start New Debate")
        
        # Display selected bot personalities
        personality_a = personalities.get(st.session_state.debate_personality_a, {})
        personality_b = personalities.get(st.session_state.debate_personality_b, {})
        
        st.info(f"🔵 **Bot A:** {personality_a.get('name', 'Bot A')} vs 🔴 **Bot B:** {personality_b.get('name', 'Bot B')}")
        
        # Real-time initial claim input
        initial_claim = st.text_input(
            "Initial Claim:",
            placeholder="Enter the statement that one bot will start with...",
            help="This will be the opening statement for the debate",
            disabled=st.session_state.debate_generating,
            key="initial_claim_text"
        )
        
        # Bot selection and start button layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            starting_bot = st.radio(
                "Which bot starts with this claim?",
                options=["🔵 Bot A", "🔴 Bot B"],
                horizontal=True,
                disabled=st.session_state.debate_generating,
                format_func=lambda x: x.split(" ", 1)[1]  # Show just "Bot A" / "Bot B"
            )
            starting_bot_key = "A" if "Bot A" in starting_bot else "B"
        
        with col2:
            # Start button with immediate state management
            button_disabled = not initial_claim.strip() or st.session_state.debate_generating
            button_text = "🚀 Start Debate" if not st.session_state.debate_generating else "🔄 Starting..."
            
            st.write("")  # Alignment spacing
            if st.button(button_text, type="primary", use_container_width=True, disabled=button_disabled):
                # Immediate state change for UI responsiveness
                st.session_state.debate_generating = True
                st.session_state.initial_claim = initial_claim
                st.session_state.selected_starting_bot = starting_bot_key
                st.rerun()
        
        # Help text for disabled button
        if not initial_claim.strip():
            st.info("💡 Enter an initial claim above to start the debate")
    
    else:
        # Debate Phase: Show active debate interface
        if st.session_state.debate_generating and not st.session_state.debate_history:
            # Starting state before first responses
            st.subheader("🔄 Starting Debate...")
            st.info("Generating initial responses...")
            
            # Initialize debate if needed
            if hasattr(st.session_state, 'initial_claim') and st.session_state.initial_claim:
                starting_bot_key = getattr(st.session_state, 'selected_starting_bot', 'A')
                if start_new_debate_with_auto_response(st.session_state.initial_claim, starting_bot_key):
                    pass  # Generation will continue automatically
                else:
                    st.error("Failed to start debate. Check your configuration.")
                    st.session_state.debate_generating = False
                    st.rerun()
        else:
            # Active debate with history
            st.subheader("🔥 Debate in Progress")
        
        # Display chat history
        if st.session_state.debate_history:
            for message in st.session_state.debate_history:
                display_debate_message(message, personalities)
        
        # Handle ongoing generation
        if st.session_state.debate_generating:
            generate_next_debate_turn()
        
        # Continue debate controls
        if len(st.session_state.debate_history) >= 2:
            st.divider()
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                # Button with explicit placeholder control
                button_placeholder = st.empty()
                
                if not st.session_state.debate_generating:
                    with button_placeholder.container():
                        if st.button(
                            "▶️ Continue Debate", 
                            type="primary", 
                            use_container_width=True,
                            key="continue_active"
                        ):
                            # Immediate button removal and state change
                            button_placeholder.empty()
                            st.session_state.debate_generating = True
                            st.session_state.turns_remaining = st.session_state.turns_per_button
                            st.session_state.turns_completed = 0
                            st.rerun()

def start_new_debate_with_auto_response(initial_claim: str, starting_bot: str = "A") -> bool:
    """
    Start a new bot vs bot debate with automatic initial response generation.
    
    This function initiates a debate and automatically generates the first two turns:
    1. The starting bot makes the initial claim
    2. The other bot automatically responds once
    3. Then manual "Continue Debate" button control takes over
    
    Args:
        initial_claim: The opening statement for the debate
        starting_bot: Which bot starts ("A" or "B")
        
    Returns:
        bool: True if debate started successfully, False otherwise
        
    The auto-response feature provides immediate engagement by showing
    a real back-and-forth exchange before requiring user interaction.
    """
    if not st.session_state.debate_initialized:
        if not setup_debate_bots():
            return False
    
    try:
        # Start the debate normally
        st.session_state.debate_manager.start_debate(initial_claim, starting_bot)
        st.session_state.debate_history = st.session_state.debate_manager.get_debate_history()
        
        # Mark that we need to auto-generate the second response
        st.session_state.auto_respond_next = True
        st.session_state.debate_generating = True
        
        return True
    except Exception as e:
        st.error(f"❌ Error starting debate: {e}")
        return False

def generate_next_debate_turn():
    """
    Handle the next turn generation in bot vs bot mode with progress tracking.
    
    This function manages the complex turn generation logic including:
    - Streaming response generation with real-time display
    - Multi-turn generation (1-10 turns per button press)
    - Auto-response for initial debate setup
    - Progress tracking and state management
    - Proper cleanup when generation completes
    
    The function handles three scenarios:
    1. Auto-response mode: Generates second turn automatically after initial claim
    2. Multi-turn mode: Generates N turns based on user setting
    3. Single turn mode: Generates one turn and stops
    
    Progress is tracked via turns_remaining and turns_completed for UI feedback.
    """
    if not st.session_state.debate_manager:
        st.error("❌ Debate manager not initialized")
        st.session_state.debate_generating = False
        return
    
    # Get info about which bot is responding
    current_turn = st.session_state.debate_manager.current_turn
    personalities = st.session_state.personalities
    
    responding_personality_key = (st.session_state.debate_personality_a if current_turn == "A" 
                                 else st.session_state.debate_personality_b)
    responding_personality = personalities.get(responding_personality_key, {})
    base_avatar = responding_personality.get("emoji", "🤖")
    personality_name = responding_personality.get("name", "Bot")
    
    # Use consistent naming with display_debate_message
    if current_turn == "A":
        avatar = "🔵"
        name = f"Bot A ({personality_name}) {base_avatar}"
    else:  # current_turn == "B"
        avatar = "🔴"
        name = f"Bot B ({personality_name}) {base_avatar}"
    
    # Display the response as it's being generated
    with st.chat_message("assistant", avatar=avatar):
        st.caption(f"*{name} is thinking...*")
        
        # Create placeholders
        thoughts_placeholder = st.empty()
        response_placeholder = st.empty()
        
        full_response = ""
        all_thoughts = ""
        
        # Show initial state
        if st.session_state.show_thoughts:
            with thoughts_placeholder.container():
                with st.expander(f"💭 {name}'s Thinking", expanded=False):
                    st.write("*Thinking...*")
        else:
            response_placeholder.write("*Generating response...*")
        
        # Stream the response
        try:
            async def stream_and_update():
                nonlocal full_response, all_thoughts
                async for content, is_thought, bot_key in get_next_debate_turn():
                    if is_thought:
                        all_thoughts += content
                        if st.session_state.show_thoughts:
                            with thoughts_placeholder.container():
                                with st.expander(f"💭 {name}'s Thinking", expanded=False):
                                    st.write(all_thoughts)
                    else:
                        full_response += content
                        if full_response.strip():
                            response_placeholder.write(full_response)
            
            # Run the streaming
            asyncio.run(stream_and_update())
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            response_placeholder.write(error_msg)
    
    # Check if we need to auto-generate another response (for the initial exchange)
    if hasattr(st.session_state, 'auto_respond_next') and st.session_state.auto_respond_next:
        st.session_state.auto_respond_next = False
        # Don't mark generation as complete yet - we need one more response
        st.rerun()
    elif hasattr(st.session_state, 'turns_remaining') and st.session_state.turns_remaining > 1:
        # More turns to generate
        st.session_state.turns_remaining -= 1
        st.session_state.turns_completed += 1
        st.rerun()
    else:
        # Mark generation as complete
        st.session_state.debate_generating = False
        st.session_state.turns_remaining = 0
        # Complete the final turn
        if hasattr(st.session_state, 'turns_completed'):
            st.session_state.turns_completed += 1
        st.rerun()

if __name__ == "__main__":
    main() 