# 🎯 Debate Bot - AI-Powered Debate Platform

A sophisticated Streamlit application that enables engaging debates between humans and AI bots, or between two AI bots with different personalities. Built with Google's Gemini API for natural language generation.

## ✨ Features

### 🤖 Dual Mode Interface
- **Human vs Bot**: Interactive debates with customizable AI personalities
- **Bot vs Bot**: Automated debates between two AI personalities with configurable generation

### 🎭 Personality System
- Multiple debate personalities (debate_bro, debate_sis, etc.)
- JSON-based configuration for easy customization
- Distinct visual indicators (emojis, names) for each personality

### ⚡ Advanced Generation
- **Real-time streaming** responses with thinking process visibility
- **Multi-turn generation**: 1-10 turns per button press
- **Configurable creativity** via temperature settings (0.0-2.0)
- **Progress tracking** with visual indicators

### 💾 Data Management
- **Save/Load** conversation states (JSON format)
- **Export** debates to readable Markdown
- **Session persistence** with proper state management

### 📱 User Experience
- **Responsive design** optimized for desktop and mobile
- **Immediate UI feedback** - buttons respond instantly to clicks
- **Clean state transitions** between setup and active debate phases
- **Collapsible thinking panels** (collapsed by default)

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   Create a `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Run Application**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Start Debating!**
   - Choose Human vs Bot or Bot vs Bot mode
   - Configure personalities and settings in sidebar
   - Enter initial claim and start debating

## 🏗️ Architecture

### Core Components
- **Frontend**: Streamlit with custom CSS and responsive design
- **Backend**: ChatBot and BotDebateManager classes (chatbot.py)
- **AI Model**: Google Gemini via official API
- **Configuration**: JSON-based personality and prompt system

### State Management
- Streamlit session state with proper cleanup
- Immediate UI updates via strategic `st.rerun()` calls
- Separate sidebar contexts for each mode

### Key Files
- `streamlit_app.py` - Main application interface
- `chatbot.py` - Core AI interaction classes
- `personalities.json` - Bot personality configurations
- `prompts/` - External prompt files for personalities

## 🎛️ Configuration

### Personality System
Edit `personalities.json` to customize bot personalities:
```json
{
  "debate_bro": {
    "name": "Debate Bro",
    "emoji": "🎯",
    "description": "Aggressive, confident debater",
    "prompt_file": "prompts/debate_bro.txt"
  }
}
```

### Temperature Settings
- **0.0-0.3**: Focused, deterministic responses
- **0.5-0.8**: Balanced creativity and consistency  
- **1.0-2.0**: Highly creative and varied responses

## 🔧 Technical Improvements

### Version 2.0 Enhancements
- **Immediate UI Responsiveness**: Buttons hide/disable instantly on click
- **Progress Tracking**: Visual progress bars for multi-turn generation
- **Clean State Management**: Eliminated circular dependencies
- **Improved Architecture**: Separate sidebar/interface functions
- **Better Documentation**: Comprehensive function documentation
- **Mobile Optimization**: Responsive design improvements

### Bug Fixes
- Fixed text input real-time updates (text_input vs text_area)
- Resolved button state management issues
- Eliminated race conditions in UI updates
- Proper cleanup of session state variables

## 📊 Bot vs Bot Features

### Smart Generation Flow
1. **Initial Setup**: Real-time claim input with instant button updates
2. **Auto Start**: First two turns generate automatically
3. **Manual Control**: Continue with configurable turn counts
4. **Progress Tracking**: Visual feedback during multi-turn generation

### Visual Distinction
- **Bot A**: 🔵 Blue indicator
- **Bot B**: 🔴 Red indicator
- Clear naming: "Bot A (Personality Name) 🎭"

## 🤝 Contributing

The codebase is well-documented and modular. Key areas for contribution:
- New personality types in `personalities.json`
- Additional prompt templates in `prompts/`
- UI/UX improvements in `streamlit_app.py`
- Core functionality in `chatbot.py`

## 📄 License

Open source - feel free to use and modify for your projects!

## 🎯 Future Enhancements

- Voice input/output support
- Debate scoring system
- Historical debate analytics
- Custom prompt creation interface
- Integration with other AI models