# Voice Blog Bot

A Telegram bot that transforms your voice messages into formatted blog posts. Record your thoughts throughout the day, and have them automatically transcribed, compiled, and published to your blog.

![Voice Blog Bot](https://img.shields.io/badge/Voice%20Blog-Bot-blue?style=for-the-badge&logo=telegram)

## Features

- 🎤 Record voice messages in Telegram
- 🔤 Speech-to-text transcription
- ✍️ AI-powered content formatting with Claude 3.7
- 📅 Daily compilation of your voice notes
- 🚀 Direct publishing to Ghost, WordPress, or Medium
- 🕒 Scheduled or on-demand publishing

## How It Works

1. **Record** your thoughts as voice messages throughout the day
2. **Transcribe** those messages automatically using speech recognition
3. **Compile** them at a scheduled time or on-demand with `/compile` command
4. **Format** them into a coherent blog post using Claude 3.7 Sonnet via OpenRouter
5. **Publish** directly to your blog platform of choice

## Installation

1. Clone this repository:

```bash
git clone https://github.com/nickg8z/voice-blog-bot.git
cd voice-blog-bot
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install FFmpeg (required for audio processing):

   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. Create a `.env` file with your credentials:

```
# Telegram Bot Token from BotFather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenRouter API Key for accessing Claude 3.7 Sonnet
OPENROUTER_API_KEY=your_openrouter_api_key

# Your Telegram User ID (to ensure only you can use the bot)
ALLOWED_USER_ID=your_telegram_user_id

# Blog platform configuration
BLOG_PLATFORM=ghost  # or wordpress, medium
BLOG_API_URL=your_blog_url
BLOG_API_KEY=your_blog_api_key
```

## Usage

1. Start the bot:

```bash
python bot.py
```

2. In Telegram, find your bot and send it voice messages throughout the day

3. The bot will automatically compile your voice messages at 9 PM, or you can use the `/compile` command to do it manually

4. The formatted blog post will be published to your blog platform

## Commands

- `/start` - Start the bot and see welcome message
- `/compile` - Manually compile today's voice messages into a blog post
- `/status` - Check how many voice messages you've sent today

## Supported Blog Platforms

Currently supported blogging platforms:

- **Ghost** - Uses JWT authentication with the Admin API
- **WordPress** - Uses the WordPress REST API
- **Medium** - Uses the Medium API

## Requirements

- Python 3.8 or higher
- FFmpeg for audio processing
- A Telegram bot token (from [@BotFather](https://t.me/botfather))
- An OpenRouter API key (for accessing Claude 3.7)
- API access to your blogging platform

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram API
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) for voice transcription
- [Anthropic's Claude](https://www.anthropic.com/claude) for AI-powered formatting
- [OpenRouter](https://openrouter.ai/) for API access to Claude

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
