# 🎯 Debate Bot

A sophisticated debate chatbot powered by Google's Gemini 2.5 Flash Preview with thinking capabilities. Features a contrarian debate agent designed to challenge and stress-test your arguments with intelligent, ruthless precision.

## ✨ Features

- **Contrarian Debate Agent**: Hyper-rational AI that challenges every claim
- **Real-time Thinking**: See the bot's reasoning process in real-time
- **Multiple Personalities**: Easy-to-manage personality system with external prompt files
- **Streamlit Interface**: Beautiful web interface with live chat
- **Terminal Interface**: Command-line interface for quick debates
- **Conversation History**: Maintains context throughout debates

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
   python debate_bot.py
   ```

## 🎭 Managing Personalities

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
# Edit the debate bro prompt
nano prompts/debate_bro.txt
```

No need to escape quotes or deal with JSON formatting!

### Current Personalities

- **💪 Debate Bro**: Contrarian, hyper-rational debate agent that challenges every claim with ruthless precision

## 🛠️ Architecture

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

### Effective Debating

- **Be Specific**: The bot challenges vague claims - define your terms clearly
- **Expect Pushback**: The bot assumes you're wrong and will find flaws
- **Stay Engaged**: Short, focused responses work best for rapid back-and-forth
- **Watch the Thinking**: Enable thinking mode to see how the bot analyzes your arguments

### Customizing Behavior

Edit `prompts/debate_bro.txt` to adjust:
- Tone and aggressiveness
- Response length preferences  
- Focus areas (logic, evidence, definitions)
- Debate style (Socratic, adversarial, etc.)

## 🔧 Development

The project uses:
- **Google Gemini 2.5 Flash Preview** for AI responses with thinking
- **Streamlit** for the web interface
- **asyncio** for streaming responses
- **Simple file-based configuration** for easy personality management

## 📝 License

MIT License - feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create new personalities in the `prompts/` directory
3. Test your changes
4. Submit a pull request

---

*Challenge everything. Question assumptions. Debate fearlessly.* 🎯