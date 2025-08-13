# 🤖 AI API Keys Setup Guide

## 📋 Required API Keys

### 1. OpenAI API Key (for GPT-4 analysis)
1. Go to: https://platform.openai.com/api-keys
2. Sign up/login to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with sk-...)
5. Add to .env file: `OPENAI_API_KEY=sk-your-key-here`

### 2. Anthropic API Key (for Claude analysis)
1. Go to: https://console.anthropic.com/
2. Sign up/login to your Anthropic account
3. Go to API Keys section
4. Create new key
5. Copy the key (starts with sk-ant-...)
6. Add to .env file: `ANTHROPIC_API_KEY=sk-ant-your-key-here`

## 💰 Pricing (as of 2024)
- **OpenAI GPT-4o-mini**: ~$0.15/1M tokens (very affordable)
- **Anthropic Claude Haiku**: ~$0.25/1M tokens
- **Daily usage**: Typically $0.10-$1.00 for trading signals

## 🚀 Quick Start
1. Get at least one API key (OpenAI recommended)
2. Add to .env file
3. Run: `python start_ai_bot.py`
4. Bot will use AI for market analysis!

## 🔄 Fallback
If no API keys: Bot uses advanced technical analysis instead.
