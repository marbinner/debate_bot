import os
import asyncio
import json
import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_prompt_from_file(prompt_file: str) -> str:
    """Load system prompt from an external file."""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Prompt file not found: {prompt_file}")
        return ""
    except Exception as e:
        print(f"❌ Error reading prompt file {prompt_file}: {e}")
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
        print("❌ personalities.json file not found")
        return {}
    except json.JSONDecodeError:
        print("❌ Error reading personalities.json file")
        return {}

class ChatBot:
    """
    A general-purpose chatbot using Google's Gemini 2.5 Flash Preview with thinking capabilities.
    Behavior is configured through system prompts and personality settings.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-preview-05-20", temperature: float = 1.0):
        """
        Initialize the ChatBot with API key and model configuration.
        
        Args:
            api_key: Google API key for Gemini
            model_name: The Gemini model to use
            temperature: Temperature for response generation (0.0-2.0)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = ""  # Will be set by personality system
    
    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def update_temperature(self, temperature: float):
        """Update the temperature setting."""
        self.temperature = max(0.0, min(2.0, temperature))  # Clamp between 0.0 and 2.0
    
    async def generate_response_stream(
        self, 
        user_message: str, 
        include_thoughts: bool = True
    ) -> AsyncGenerator[Tuple[str, bool], None]:
        """
        Generate a streaming response to the user's message.
        
        Args:
            user_message: The user's input message
            include_thoughts: Whether to include thought summaries
            
        Yields:
            Tuple of (content, is_thought) where is_thought indicates if it's a thought or response
        """
        # Add user message to history
        self.add_to_history("user", user_message)
        
        # Prepare the full conversation context for the API with proper message structure
        conversation_messages = []
        for msg in self.conversation_history:
            # Convert to proper message format for Gemini API
            if msg["role"] == "user":
                conversation_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            else:  # assistant
                conversation_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
        
        # Handle edge case where no conversation history exists
        if not conversation_messages:
            conversation_messages = [{"role": "user", "parts": [{"text": user_message}]}]
        
        try:
            # Configure thinking and generation settings
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=include_thoughts
                ),
                system_instruction=self.system_prompt,
                temperature=self.temperature,
                max_output_tokens=8192 * 4
            )
            
            # Stream the response with full conversation context
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=conversation_messages,  # Pass properly structured conversation history
                config=config
            )
            
            full_response = ""
            response_generated = False
            
            for chunk in response_stream:
                if chunk.candidates and len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.text:
                                response_generated = True
                                if hasattr(part, 'thought') and part.thought:
                                    # This is a thought
                                    yield (part.text, True)
                                else:
                                    # This is the actual response
                                    full_response += part.text
                                    yield (part.text, False)
            
            # Handle case where no response was generated
            if not response_generated:
                error_message = "No response generated by the model"
                yield (error_message, False)
                full_response = error_message
            
            # Add the complete response to history only if we have content
            if full_response.strip():
                self.add_to_history("assistant", full_response)
                
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            yield (error_message, False)
            self.add_to_history("assistant", error_message)
    
    async def generate_response(
        self, 
        user_message: str, 
        include_thoughts: bool = True
    ) -> Tuple[str, Optional[str]]:
        """
        Generate a complete response to the user's message.
        
        Args:
            user_message: The user's input message
            include_thoughts: Whether to include thought summaries
            
        Returns:
            Tuple of (response_text, thought_summary)
        """
        # Add user message to history
        self.add_to_history("user", user_message)
        
        # Prepare the full conversation context for the API with proper message structure
        conversation_messages = []
        for msg in self.conversation_history:
            # Convert to proper message format for Gemini API
            if msg["role"] == "user":
                conversation_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            else:  # assistant
                conversation_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
        
        # Handle edge case where no conversation history exists
        if not conversation_messages:
            conversation_messages = [{"role": "user", "parts": [{"text": user_message}]}]
        
        try:
            # Configure thinking and generation settings
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=include_thoughts
                ),
                system_instruction=self.system_prompt,
                temperature=self.temperature,
                max_output_tokens=8192
            )
            
            # Generate the response with full conversation context
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=conversation_messages,  # Pass properly structured conversation history
                config=config
            )
            
            response_text = ""
            thought_summary = None
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.text:
                            if hasattr(part, 'thought') and part.thought:
                                thought_summary = part.text
                            else:
                                response_text += part.text
            
            # Handle case where no response was generated
            if not response_text.strip():
                response_text = "No response generated by the model"
            
            # Add the response to history only if we have content
            if response_text.strip():
                self.add_to_history("assistant", response_text)
            
            return response_text, thought_summary
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            self.add_to_history("assistant", error_message)
            return error_message, None
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def update_system_prompt(self, new_prompt: str):
        """Update the system prompt."""
        self.system_prompt = new_prompt
    
    def save_conversation_state(self, filepath: str, additional_metadata: Optional[Dict] = None) -> bool:
        """
        Save the complete conversation state to a JSON file.
        
        Args:
            filepath: Path where to save the conversation state
            additional_metadata: Optional additional metadata to save with the state
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            state = {
                "version": "1.0",
                "timestamp": datetime.datetime.now().isoformat(),
                "model_name": self.model_name,
                "temperature": self.temperature,
                "system_prompt": self.system_prompt,
                "conversation_history": self.conversation_history.copy(),
                "metadata": additional_metadata or {}
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Error saving conversation state: {e}")
            return False
    
    def load_conversation_state(self, filepath: str) -> Tuple[bool, Optional[Dict]]:
        """
        Load conversation state from a JSON file.
        
        Args:
            filepath: Path to the saved conversation state file
            
        Returns:
            Tuple of (success, metadata) where success is True if load was successful,
            and metadata contains any additional saved metadata
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Validate state format
            required_fields = ["conversation_history", "system_prompt", "temperature"]
            for field in required_fields:
                if field not in state:
                    print(f"❌ Invalid state file: missing field '{field}'")
                    return False, None
            
            # Load state into current instance
            self.conversation_history = state["conversation_history"]
            self.system_prompt = state["system_prompt"]
            self.temperature = state["temperature"]
            
            # Update model name if present and different
            if "model_name" in state and state["model_name"] != self.model_name:
                print(f"⚠️ Note: Loaded state was created with model '{state['model_name']}', "
                      f"currently using '{self.model_name}'")
            
            metadata = state.get("metadata", {})
            print(f"✅ Successfully loaded conversation with {len(self.conversation_history)} messages")
            
            return True, metadata
            
        except FileNotFoundError:
            print(f"❌ Conversation state file not found: {filepath}")
            return False, None
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in state file: {filepath}")
            return False, None
        except Exception as e:
            print(f"❌ Error loading conversation state: {e}")
            return False, None
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of the current conversation state."""
        return {
            "message_count": len(self.conversation_history),
            "user_messages": len([msg for msg in self.conversation_history if msg["role"] == "user"]),
            "assistant_messages": len([msg for msg in self.conversation_history if msg["role"] == "assistant"]),
            "temperature": self.temperature,
            "has_system_prompt": bool(self.system_prompt.strip()),
            "system_prompt_preview": self.system_prompt[:100] + "..." if len(self.system_prompt) > 100 else self.system_prompt
        }

class BotDebateManager:
    """
    Manages debates between two bot personalities.
    Each bot maintains their own conversation history and thinks the other bot is a human.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-preview-05-20"):
        """
        Initialize the debate manager with two bot instances.
        
        Args:
            api_key: Google API key for Gemini
            model_name: The Gemini model to use for both bots
        """
        self.api_key = api_key
        self.model_name = model_name
        self.bot_a = None
        self.bot_b = None
        self.personality_a = None
        self.personality_b = None
        self.debate_history = []  # Combined history for display
        self.current_turn = "A"  # Which bot goes next
        self.turn_count = 0
    
    def setup_debate(
        self, 
        personality_a_key: str, 
        personality_a_prompt: str,
        personality_b_key: str, 
        personality_b_prompt: str,
        temperature_a: float = 1.0,
        temperature_b: float = 1.0
    ):
        """
        Set up the two bots with their personalities.
        
        Args:
            personality_a_key: Key for personality A
            personality_a_prompt: System prompt for bot A
            personality_b_key: Key for personality B  
            personality_b_prompt: System prompt for bot B
            temperature_a: Temperature for bot A
            temperature_b: Temperature for bot B
        """
        try:
            # Initialize both bots
            self.bot_a = ChatBot(self.api_key, self.model_name, temperature_a)
            self.bot_b = ChatBot(self.api_key, self.model_name, temperature_b)
            
            # Set up their personalities
            self.bot_a.update_system_prompt(personality_a_prompt)
            self.bot_b.update_system_prompt(personality_b_prompt)
            
            # Store personality info
            self.personality_a = personality_a_key
            self.personality_b = personality_b_key
            
            return True
        except Exception as e:
            print(f"❌ Error setting up debate: {e}")
            return False
    
    def start_debate(self, initial_claim: str, starting_bot: str = "A"):
        """
        Start the debate with an initial claim.
        
        Args:
            initial_claim: The initial statement to debate
            starting_bot: Which bot starts ("A" or "B")
        """
        self.debate_history = []
        self.turn_count = 0
        self.current_turn = starting_bot
        
        # Add the initial claim to the debate history
        self.debate_history.append({
            "bot": starting_bot,
            "personality": self.personality_a if starting_bot == "A" else self.personality_b,
            "content": initial_claim,
            "thought": None,
            "turn": self.turn_count
        })
        
        # Add initial claim to the starting bot's history
        starting_bot_instance = self.bot_a if starting_bot == "A" else self.bot_b
        starting_bot_instance.add_to_history("assistant", initial_claim)
        
        # Set next turn to the other bot
        self.current_turn = "B" if starting_bot == "A" else "A"
        self.turn_count += 1
    
    async def next_turn(self, include_thoughts: bool = True) -> Tuple[str, Optional[str], str]:
        """
        Generate the next response in the debate.
        
        Args:
            include_thoughts: Whether to include thought processes
            
        Returns:
            Tuple of (response_text, thought_summary, responding_bot)
        """
        if not self.bot_a or not self.bot_b:
            raise ValueError("Debate not properly set up. Call setup_debate() first.")
        
        if not self.debate_history:
            raise ValueError("Debate not started. Call start_debate() first.")
        
        # Get the last message from the other bot
        last_message = self.debate_history[-1]
        last_content = last_message["content"]
        
        # Determine which bot responds
        responding_bot = self.bot_a if self.current_turn == "A" else self.bot_b
        responding_bot_key = self.current_turn
        responding_personality = self.personality_a if self.current_turn == "A" else self.personality_b
        
        try:
            # Generate response
            response_text, thought_summary = await responding_bot.generate_response(
                last_content, include_thoughts=include_thoughts
            )
            
            # Add to debate history
            self.debate_history.append({
                "bot": responding_bot_key,
                "personality": responding_personality,
                "content": response_text,
                "thought": thought_summary,
                "turn": self.turn_count
            })
            
            # Add the response to the other bot's history as a "user" message
            # This makes each bot think the other is a human
            other_bot = self.bot_b if self.current_turn == "A" else self.bot_a
            other_bot.add_to_history("user", response_text)
            
            # Switch turns
            self.current_turn = "B" if self.current_turn == "A" else "A"
            self.turn_count += 1
            
            return response_text, thought_summary, responding_bot_key
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            return error_message, None, responding_bot_key
    
    async def next_turn_stream(self, include_thoughts: bool = True):
        """
        Generate the next response in the debate with streaming.
        
        Args:
            include_thoughts: Whether to include thought processes
            
        Yields:
            Tuple of (content, is_thought, responding_bot_key)
        """
        if not self.bot_a or not self.bot_b:
            raise ValueError("Debate not properly set up. Call setup_debate() first.")
        
        if not self.debate_history:
            raise ValueError("Debate not started. Call start_debate() first.")
        
        # Get the last message from the other bot
        last_message = self.debate_history[-1]
        last_content = last_message["content"]
        
        # Determine which bot responds
        responding_bot = self.bot_a if self.current_turn == "A" else self.bot_b
        responding_bot_key = self.current_turn
        responding_personality = self.personality_a if self.current_turn == "A" else self.personality_b
        
        full_response = ""
        all_thoughts = ""
        
        try:
            # Stream the response
            async for content, is_thought in responding_bot.generate_response_stream(
                last_content, include_thoughts=include_thoughts
            ):
                if is_thought:
                    all_thoughts += content
                else:
                    full_response += content
                
                yield content, is_thought, responding_bot_key
            
            # Add to debate history
            self.debate_history.append({
                "bot": responding_bot_key,
                "personality": responding_personality,
                "content": full_response,
                "thought": all_thoughts.strip() if all_thoughts.strip() else None,
                "turn": self.turn_count
            })
            
            # Add the response to the other bot's history as a "user" message
            other_bot = self.bot_b if self.current_turn == "A" else self.bot_a
            other_bot.add_to_history("user", full_response)
            
            # Switch turns
            self.current_turn = "B" if self.current_turn == "A" else "A"
            self.turn_count += 1
            
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            yield error_message, False, responding_bot_key
    
    def get_debate_history(self) -> List[Dict]:
        """Get the complete debate history."""
        return self.debate_history.copy()
    
    def get_debate_summary(self) -> Dict:
        """Get a summary of the current debate state."""
        return {
            "total_turns": len(self.debate_history),
            "current_turn": self.current_turn,
            "turn_count": self.turn_count,
            "personality_a": self.personality_a,
            "personality_b": self.personality_b,
            "bot_a_messages": len([msg for msg in self.debate_history if msg["bot"] == "A"]),
            "bot_b_messages": len([msg for msg in self.debate_history if msg["bot"] == "B"])
        }
    
    def clear_debate(self):
        """Clear the current debate and reset both bots."""
        self.debate_history = []
        self.current_turn = "A"
        self.turn_count = 0
        
        if self.bot_a:
            self.bot_a.clear_history()
        if self.bot_b:
            self.bot_b.clear_history()
    
    def export_debate_to_markdown(self, personalities_dict: Dict = None) -> str:
        """Export debate history to markdown format."""
        import datetime
        
        markdown_content = []
        markdown_content.append("# Bot vs Bot Debate")
        markdown_content.append(f"*Exported on {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
        markdown_content.append("")
        
        if personalities_dict:
            # Add personality info
            personality_a_info = personalities_dict.get(self.personality_a, {})
            personality_b_info = personalities_dict.get(self.personality_b, {})
            
            markdown_content.append("## Debate Participants")
            markdown_content.append(f"**Bot A:** {personality_a_info.get('emoji', '🤖')} {personality_a_info.get('name', 'Bot A')}")
            markdown_content.append(f"**Bot B:** {personality_b_info.get('emoji', '🤖')} {personality_b_info.get('name', 'Bot B')}")
            markdown_content.append("")
        
        if not self.debate_history:
            markdown_content.append("*No messages in this debate.*")
            return "\n".join(markdown_content)
        
        # Process each message
        for message in self.debate_history:
            bot_key = message["bot"]
            content = message["content"]
            turn = message.get("turn", 0)
            
            # Get personality info
            if personalities_dict and message["personality"] in personalities_dict:
                personality = personalities_dict[message["personality"]]
                emoji = personality.get("emoji", "🤖")
                name = personality.get("name", f"Bot {bot_key}")
            else:
                emoji = "🤖"
                name = f"Bot {bot_key}"
            
            markdown_content.append(f"## Turn {turn + 1}: {emoji} {name}")
            markdown_content.append(content)
            markdown_content.append("")
        
        return "\n".join(markdown_content)

# Interactive terminal interface
if __name__ == "__main__":
    import asyncio
    
    def print_colored(text, color="white"):
        """Print colored text to terminal."""
        colors = {
            "red": "\033[91m",
            "green": "\033[92m", 
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m"
        }
        print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")
    
    async def run_terminal_interface():
        """Run the interactive terminal interface."""
        print_colored("🎯 DEBATE BOT - Terminal Interface", "purple")
        print_colored("=" * 50, "cyan")
        
        # Load personalities
        personalities = load_personalities()
        if not personalities:
            print_colored("❌ No personalities found. Using default system prompt.", "red")
            default_prompt = "You are a helpful AI assistant."
        else:
            # Use debate_bro personality if available, otherwise first available
            if "debate_bro" in personalities:
                current_personality = personalities["debate_bro"]
                print_colored(f"✅ Using personality: {current_personality['name']}", "green")
            else:
                current_personality = list(personalities.values())[0]
                print_colored(f"✅ Using personality: {current_personality['name']}", "green")
            default_prompt = current_personality["system_prompt"]
        
        # Initialize bot
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print_colored("❌ ERROR: Please set GOOGLE_API_KEY environment variable", "red")
            print_colored("Create a .env file with: GOOGLE_API_KEY=your_api_key_here", "yellow")
            return
        
        try:
            bot = ChatBot(api_key)
            bot.update_system_prompt(default_prompt)
            print_colored("✅ Bot initialized successfully!", "green")
        except Exception as e:
            print_colored(f"❌ Failed to initialize bot: {e}", "red")
            return
        
        print_colored("\nStart chatting! Type 'quit' to exit, 'clear' to reset conversation.", "cyan")
        print_colored("Commands: 'save <filename>' to save conversation, 'load <filename>' to load conversation", "cyan")
        print_colored("=" * 50, "cyan")
        
        while True:
            try:
                # Get user input
                print_colored("\n👤 You:", "blue")
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print_colored("\n👋 Thanks for chatting! Goodbye!", "green")
                    break
                    
                if user_input.lower() in ['clear', 'reset']:
                    bot.clear_history()
                    print_colored("🗑️ Conversation cleared!", "yellow")
                    continue
                
                # Handle save command
                if user_input.lower().startswith('save '):
                    filename = user_input[5:].strip()
                    if not filename:
                        print_colored("❌ Please provide a filename. Usage: save <filename>", "red")
                        continue
                    
                    if not filename.endswith('.json'):
                        filename += '.json'
                    
                    # Add current personality to metadata
                    metadata = {
                        "current_personality": current_personality.get("name", "Unknown") if 'current_personality' in locals() else "Unknown",
                        "saved_from": "terminal_interface"
                    }
                    
                    if bot.save_conversation_state(filename, metadata):
                        print_colored(f"💾 Conversation saved to {filename}", "green")
                    else:
                        print_colored(f"❌ Failed to save conversation to {filename}", "red")
                    continue
                
                # Handle load command
                if user_input.lower().startswith('load '):
                    filename = user_input[5:].strip()
                    if not filename:
                        print_colored("❌ Please provide a filename. Usage: load <filename>", "red")
                        continue
                    
                    if not filename.endswith('.json'):
                        filename += '.json'
                    
                    success, metadata = bot.load_conversation_state(filename)
                    if success:
                        print_colored(f"📁 Conversation loaded from {filename}", "green")
                        if metadata and "current_personality" in metadata:
                            print_colored(f"ℹ️ Original personality: {metadata['current_personality']}", "cyan")
                        
                        # Show conversation summary
                        summary = bot.get_conversation_summary()
                        print_colored(f"📊 Loaded {summary['message_count']} messages "
                                    f"({summary['user_messages']} from you, {summary['assistant_messages']} from bot)", "cyan")
                    else:
                        print_colored(f"❌ Failed to load conversation from {filename}", "red")
                    continue
                
                # Show thinking indicator
                print_colored("\n🤖 Bot is thinking...", "yellow")
                
                # Get response from bot
                response_text, thought_summary = await bot.generate_response(
                    user_input, include_thoughts=True
                )
                
                # Display response
                print_colored("\n🤖 Bot:", "purple")
                print(response_text)
                
                # Show thinking if available
                if thought_summary and thought_summary.strip():
                    print_colored("\n💭 Bot's Reasoning:", "cyan")
                    print_colored(thought_summary, "white")
                
            except KeyboardInterrupt:
                print_colored("\n\n👋 Interrupted. Goodbye!", "yellow")
                break
            except Exception as e:
                print_colored(f"\n❌ Error: {e}", "red")
    
    # Run the interface
    asyncio.run(run_terminal_interface()) 