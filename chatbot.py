import os
import asyncio
import json
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