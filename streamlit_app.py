import streamlit as st
import asyncio
import os
import json
from typing import Optional, Dict
from debate_bot import DebateBot
from dotenv import load_dotenv

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

def initialize_session_state():
    """Initialize all session state variables on first run."""
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
        
    # Auto-initialize the bot after personalities are loaded
    if not st.session_state.bot_initialized and st.session_state.personalities:
        initialize_bot()

def initialize_bot() -> bool:
    """Set up the DebateBot with API key and current personality."""
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
        st.session_state.bot = DebateBot(api_key, temperature=st.session_state.temperature)
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
                with st.expander("💭 Bot's Thinking", expanded=True):
                    st.write(thought)
            
            # Show the actual response
            st.write(content)

def main():
    """Main app interface."""
    initialize_session_state()
    
    # === SIDEBAR ===
    with st.sidebar:
        st.header("⚙️ Settings")
        
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
                disabled=st.session_state.generating
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
    
    # === MAIN CHAT INTERFACE ===
    if not st.session_state.bot_initialized:
        st.info("⚠️ Bot initialization failed. Please check your API key configuration.")
        return
    
    # Create a centered container for the chat interface
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Display chat history
        for i, message in enumerate(st.session_state.messages):
            thought = st.session_state.thoughts[i] if i < len(st.session_state.thoughts) else None
            personality_key = st.session_state.message_personalities[i] if i < len(st.session_state.message_personalities) else None
            display_message(message["role"], message["content"], thought, personality_key, i)
        
        # Chat input (disabled during generation)
        if prompt := st.chat_input("Enter your debate topic or argument...", disabled=st.session_state.generating):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.thoughts.append(None)
            st.session_state.message_personalities.append(None)
            st.session_state.generating = True
            st.rerun()  # Rerun to show user message and start generation
    
    # Generate bot response if user just sent a message
    if st.session_state.generating and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        generate_bot_response()

def generate_bot_response():
    """Handle bot response generation with real-time streaming."""
    prompt = st.session_state.messages[-1]["content"]
    
    # Get current personality for avatar and name
    current_personality = st.session_state.personalities.get(st.session_state.current_personality, {})
    current_avatar = current_personality.get("emoji", "🤖")
    current_name = current_personality.get("name", "Bot")
    
    # Create the same column layout for consistent width
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Display bot response with streaming
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
                    with st.expander("💭 Bot's Thinking", expanded=True):
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
                                    with st.expander("💭 Bot's Thinking", expanded=True):
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

if __name__ == "__main__":
    main() 