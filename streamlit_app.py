import streamlit as st
import asyncio
import os
import json
from typing import Optional, Dict, Tuple
from chatbot import ChatBot
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
    if 'state_loaded' not in st.session_state:
        st.session_state.state_loaded = False
        
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
                with st.expander("💭 Bot's Thinking", expanded=True):
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
                key="state_uploader"
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

    # === MAIN CHAT INTERFACE ===
    if not st.session_state.bot_initialized:
        st.info("⚠️ Bot initialization failed. Please check your API key configuration.")
        return
    
    # Display chat history with responsive layout
    # Use container without forced margins to utilize full width
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