# 🎯 Debate Bot

A sophisticated debate chatbot powered by Google's Gemini 2.5 Flash Preview with thinking capabilities. Features multiple contrarian debate personalities designed to challenge and stress-test your arguments with intelligent, ruthless precision.

## ✨ Features

- **Multiple Debate Personalities**: 4 unique AI personalities that challenge arguments in different ways
- **Real-time Thinking**: See the bot's reasoning process in real-time
- **Personality Switching**: Easy-to-manage personality system with external prompt files
- **Streamlit Interface**: Beautiful web interface with live chat and personality selector
- **Terminal Interface**: Command-line interface for quick debates
- **Conversation History**: Maintains context throughout debates

## 🎭 Available Personalities

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
   python debate_bot.py
   ```

## 🌐 Live Demo

Visit the live app at: [Streamlit Community Cloud](https://share.streamlit.io/) (after deployment)

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

- **Be Specific**: All personalities challenge vague claims - define your terms clearly
- **Expect Pushback**: Each bot assumes you're wrong and will find flaws in unique ways
- **Try Different Personalities**: Each offers a completely different debate experience
- **Stay Engaged**: Short, focused responses work best for rapid back-and-forth
- **Watch the Thinking**: Enable thinking mode to see how the bot analyzes your arguments

### Personality Differences

- **Debate Bro**: Hits you with pure logic and facts, no mercy
- **Debate Sis**: Destroys you with cuteness while being devastatingly logical
- **Debate Baby**: Makes you feel dumb through innocent toddler questions
- **Triggered Lib**: Attacks through moral superiority and academic credentials

### Customizing Behavior

Edit any personality file in `prompts/` to adjust:
- Tone and aggressiveness
- Response length preferences  
- Focus areas (logic, evidence, definitions)
- Debate style (Socratic, adversarial, etc.)

## 🔧 Development

The project uses:
- **Google Gemini 2.5 Flash Preview** for AI responses with thinking
- **Streamlit** for the web interface with personality selector
- **asyncio** for streaming responses
- **Simple file-based configuration** for easy personality management

## 📝 License

MIT License - feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create new personalities in the `prompts/` directory
3. Add them to `personalities.json`
4. Test your changes
5. Submit a pull request

### Ideas for New Personalities

- **Conspiracy Theorist**: Questions everything and sees hidden agendas
- **Academic Elitist**: Demands peer-reviewed sources for everything
- **Devil's Advocate**: Always takes the opposite position
- **Zen Master**: Challenges through philosophical questions

---

*Challenge everything. Question assumptions. Debate fearlessly with personality.* 🎯