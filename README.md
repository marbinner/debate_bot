# 🤖 Personality-Driven ChatBot

A general-purpose chatbot powered by Google's Gemini 2.5 Flash Preview with thinking capabilities. Features a flexible personality system that allows the bot to take on different behaviors through external prompt files. Currently includes multiple debate personalities designed to challenge and stress-test your arguments with intelligent precision.

## ✨ Features

- **Flexible Personality System**: Easily configurable AI personalities through external prompt files
- **Real-time Thinking**: See the bot's reasoning process in real-time
- **Hot-swappable Personalities**: Easy-to-manage personality system with external prompt files
- **Streamlit Interface**: Beautiful web interface with live chat and personality selector
- **Terminal Interface**: Command-line interface for quick conversations
- **Conversation History**: Maintains context throughout conversations
- **Save & Load Conversations**: Save complete conversation state and resume later with robust error handling
- **Export Functionality**: Download chat history as markdown files
- **Temperature Control**: Adjust response creativity and randomness
- **Cross-Platform State Sharing**: State files work seamlessly between terminal and web interfaces
- **Automatic State Validation**: Smart fallbacks and error recovery for corrupted or incompatible state files

## 🎭 Included Personalities (Debate Focus)

- **💪 Debate Bro**: Aggressive, hyper-rational agent who thinks you're wrong about everything and will relentlessly tear apart your arguments with zero chill
- **🌸 Debate Sis**: Cute, bubbly anime girl who dismantles your arguments with giggles and pet names. Don't let the kawaii exterior fool you - she's ruthlessly logical
- **👶 Debate Baby**: An adorable toddler who accidentally destroys your arguments with innocent questions and baby talk. Don't underestimate the devastating logical precision!
- **😤 Triggered Lib**: A hyper-progressive activist with multiple degrees who sees oppression everywhere and gets genuinely triggered by problematic statements

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key:**
   Create a `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Run the app:**
   ```bash
   # Web interface (recommended)
   streamlit run streamlit_app.py
   
   # Terminal interface
   python chatbot.py
   ```

## 🌐 Live Demo

Visit the live app at: [Streamlit Community Cloud](https://share.streamlit.io/) (after deployment)

## 🎭 Personality System

### Easy Prompt Editing

Personality prompts are stored in separate text files for easy editing:

- **Configuration**: `personalities.json` - Contains metadata and references to prompt files
- **Prompts**: `prompts/` directory - Contains the actual system prompts as plain text files

### Adding a New Personality

1. **Create a prompt file:**
   ```bash
   # Create your prompt file
   echo "Your system prompt here..." > prompts/my_personality.txt
   ```

2. **Add to personalities.json:**
   ```json
   {
     "my_personality": {
       "name": "My Personality",
       "description": "Description of the personality",
       "emoji": "🎪",
       "prompt_file": "prompts/my_personality.txt"
     }
   }
   ```

### Editing Existing Prompts

Simply edit the text files in the `prompts/` directory:

```bash
# Edit any personality prompt
nano prompts/debate_bro.txt
nano prompts/debate_baby.txt
nano prompts/triggered_lib.txt
```

No need to escape quotes or deal with JSON formatting!

### Current Personality Files

- `prompts/debate_bro.txt` - Aggressive logical destroyer
- `prompts/debate_sis.txt` - Cute but ruthless anime girl
- `prompts/debate_baby.txt` - Innocent toddler with devastating questions  
- `prompts/triggered_lib.txt` - Hyper-progressive academic with moral superiority

## 🛠️ Architecture

### Core Components

- **`chatbot.py`**: General-purpose ChatBot class with Gemini API integration
- **`streamlit_app.py`**: Web interface with personality management
- **`personalities.json`**: Configuration file for all personalities
- **`prompts/`**: Directory containing system prompt files

### Prompt Loading System

The bot supports two ways to define system prompts:

1. **External Files** (recommended):
   ```json
   {
     "personality_key": {
       "name": "Name",
       "description": "Description", 
       "emoji": "🎯",
       "prompt_file": "prompts/file.txt"
     }
   }
   ```

2. **Inline** (legacy):
   ```json
   {
     "personality_key": {
       "name": "Name",
       "description": "Description",
       "emoji": "🎯", 
       "system_prompt": "Your prompt here..."
     }
   }
   ```

The system automatically detects which format you're using and loads accordingly.

## 💡 Usage Tips

### Effective Conversations

- **Be Specific**: Many personalities challenge vague claims - define your terms clearly
- **Experiment with Personalities**: Each offers a completely different conversation experience
- **Adjust Temperature**: Lower values (0.1-0.3) for consistent responses, higher (0.8-2.0) for creativity
- **Watch the Thinking**: Enable thinking mode to see how the bot analyzes your messages
- **Export Conversations**: Save interesting conversations as markdown files

### Creating New Personality Types

The system is designed to support any type of personality, not just debate-focused ones:

- **Helpful Assistant**: Traditional supportive AI helper
- **Creative Writer**: Collaborative storytelling and writing partner
- **Teacher**: Educational and explanatory responses
- **Therapist**: Supportive and reflective conversations
- **Expert Consultant**: Domain-specific expertise (law, medicine, tech, etc.)

### Customizing Behavior

Edit any personality file in `prompts/` to adjust:
- Tone and communication style
- Response length preferences  
- Focus areas and expertise
- Conversation approach and goals

## 🔧 Development

The project uses:
- **Google Gemini 2.5 Flash Preview** for AI responses with thinking
- **Streamlit** for the web interface with personality management
- **asyncio** for streaming responses
- **Simple file-based configuration** for easy personality management

### Recent Improvements

- **Robust State Management**: Complete save/load system with automatic validation
- **Error Recovery**: Smart fallbacks for corrupted or incompatible state files
- **Cross-Platform Compatibility**: Seamless state sharing between interfaces
- **Performance Optimizations**: Reduced memory usage and faster loading
- **User Experience**: Better feedback, loading indicators, and error messages

### Architecture Overview

```
debate_bot/
├── chatbot.py              # Core ChatBot class with Gemini integration
├── streamlit_app.py        # Web interface with state management
├── personalities.json     # Personality configuration
├── prompts/               # Individual personality prompt files
├── example_conversation_state.json  # Example state file
├── requirements.txt       # Python dependencies
└── .env                  # API keys (create this file)
```

### Key Components

- **ChatBot Class**: Handles conversation, thinking, and state persistence
- **Personality System**: Modular prompt loading with hot-swapping
- **State Management**: JSON-based conversation persistence with validation
- **Streaming Interface**: Real-time response generation with thinking display

## 📝 License

MIT License - feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create new personalities in the `prompts/` directory
3. Add them to `personalities.json`
4. Test your changes
5. Submit a pull request

### Ideas for New Personalities

**Debate & Challenge:**
- **Conspiracy Theorist**: Questions everything and sees hidden agendas
- **Academic Elitist**: Demands peer-reviewed sources for everything
- **Devil's Advocate**: Always takes the opposite position

**Helpful & Supportive:**
- **Life Coach**: Motivational and goal-oriented guidance
- **Therapist**: Empathetic listening and reflection
- **Teacher**: Educational explanations and examples

**Creative & Fun:**
- **Storyteller**: Creative writing and worldbuilding
- **Game Master**: RPG and interactive story facilitation
- **Comedy Writer**: Humor and witty banter

**Expert Consultants:**
- **Tech Expert**: Programming and technology guidance
- **Business Advisor**: Strategic and operational advice
- **Fitness Coach**: Health and wellness guidance

---

*Build any conversational AI personality with simple text files.* 🤖

## 💾 Save & Load Conversations

### Full State Management

The bot now supports saving and loading complete conversation states, allowing you to:

- **Continue conversations** exactly where you left off
- **Share conversation states** with others
- **Archive interesting discussions** for later reference
- **Switch between devices** while maintaining conversation context

### What Gets Saved

When you save a conversation state, it includes:
- **All messages** (user and bot responses)
- **Thinking processes** (if available)
- **Personality history** (which personality responded to each message)
- **Current settings** (personality, temperature, thinking visibility)
- **Metadata** (timestamps, message counts, export source)

### How to Use

#### Streamlit Interface

1. **Save Current Conversation:**
   - Navigate to the "💾 Save & Load" section in the sidebar
   - Click "💾 Save State" to download a `.json` file with complete conversation state
   - Click "📄 Export MD" to download a readable markdown version (no state info)

2. **Load Previous Conversation:**
   - Use the file uploader in the "💾 Save & Load" section
   - Select a previously saved `.json` state file
   - The conversation will be restored with all original settings

3. **Clear Conversation:**
   - Click "🗑️ Clear Conversation" to start fresh

#### Terminal Interface

1. **Save conversation:**
   ```
   save my_conversation
   # or
   save my_conversation.json
   ```

2. **Load conversation:**
   ```
   load my_conversation
   # or  
   load my_conversation.json
   ```

3. **Clear conversation:**
   ```
   clear
   # or
   reset
   ```

### File Formats

#### State File (.json)
Complete conversation state with all metadata:
```json
{
  "version": "1.0",
  "timestamp": "2024-12-19T10:30:00.000000",
  "current_personality": "debate_bro",
  "temperature": 1.2,
  "show_thoughts": true,
  "messages": [...],
  "thoughts": [...],
  "message_personalities": [...],
  "metadata": {...}
}
```

#### Markdown Export (.md)
Human-readable conversation transcript:
```markdown
# Debate Bot Chat History
*Exported on 2024-12-19 at 10:30:00*

## 👤 You
Your message here...

## 💪 Debate Bro  
Bot response here...
```

### Cross-Platform Compatibility

State files are compatible between:
- **Streamlit web interface** ↔ **Terminal interface**
- **Different devices** running the same bot version
- **Shared conversations** between users (personality prompts must exist)

### Best Practices

- **Save regularly** during long conversations
- **Use descriptive filenames** (e.g., `debate_pineapple_pizza_2024.json`)
- **Keep state files** for interesting conversations you want to revisit
- **Share state files** to continue conversations on different devices

### Troubleshooting

#### Common Issues & Solutions

**File Already Loaded Message:**
- This prevents accidental re-processing of the same file
- Solution: Clear the conversation first, then upload the file again

**Personality Not Found:**
- The loaded conversation uses a personality that doesn't exist in your current setup
- Solution: The system automatically falls back to available personalities and shows a warning

**Array Length Errors (Fixed in Latest Version):**
- Previous versions had issues with mismatched message/thought arrays
- Solution: Update to latest version - automatic validation and repair included

**Upload Doesn't Work:**
- Make sure you're uploading a `.json` file (not `.md`)
- Check that the file was generated by this bot (not manually created)
- Ensure the file size is reasonable (under 10MB)

**Bot Settings Not Loading:**
- Temperature and personality should update automatically after loading
- If not, manually adjust them in the sidebar after loading

#### Recovery Options

If a state file seems corrupted:
1. Try loading it in the terminal interface first: `python chatbot.py` then `load filename.json`
2. Check the JSON syntax with an online validator
3. Use the `example_conversation_state.json` as a template for manual repairs

#### Getting Help

- Check the console output (terminal interface) for detailed error messages
- Ensure your `.env` file has a valid `GOOGLE_API_KEY`
- Verify all personality prompt files exist in the `prompts/` directory