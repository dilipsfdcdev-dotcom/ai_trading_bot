# 🚀 Quick Start - Get Running in 2 Minutes!

## Step 1: Prerequisites

Install these three things:

1. **Python 3.10+** → [Download here](https://www.python.org/downloads/)
2. **Node.js 18+** → [Download here](https://nodejs.org/)
3. **MetaTrader 5** → [Download here](https://www.metatrader5.com/)

## Step 2: Run the Bot

### On Windows:
1. Double-click `start.bat`
2. Wait for it to install dependencies (first time only)
3. Done! 🎉

### On Mac/Linux:
1. Open terminal in this folder
2. Run: `./start.sh`
3. Done! 🎉

## Step 3: Access Dashboard

Open your browser and go to:
**http://localhost:3000**

## That's It!

The bot is now running with:
- ✅ Backend API on port 8000
- ✅ Frontend dashboard on port 3000
- ✅ Real-time data streaming
- ✅ MT5 connection (if configured)

## First Time Setup Notes

### Your credentials are already configured!
The `.env` files have been created with your MT5 and API credentials.

### What the scripts do:
1. Check if Python and Node.js are installed
2. Install all required packages (first run only)
3. Start backend Python server
4. Start frontend Next.js dashboard
5. Keep both running until you press Ctrl+C

### Stopping the Bot

**Windows**: Close the command windows or press Ctrl+C

**Mac/Linux**: Press Ctrl+C in the terminal

## Next Steps

1. **Check Connection**: Make sure MT5 is running and logged in
2. **Review Settings**: Check `backend/.env` for trading parameters
3. **Start Trading**: Click "Start Trading" in the dashboard
4. **Monitor**: Watch the decision log and charts

## Need Help?

- **Detailed setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Full docs**: Check [README.md](README.md)
- **Troubleshooting**: See the troubleshooting section in README

## ⚠️ Important Safety Notes

- ✅ Always start with a DEMO account
- ✅ Test thoroughly before going live
- ✅ Never risk more than you can afford to lose
- ✅ Monitor the bot regularly
- ⚠️ Trading involves significant risk

## Configuration Quick Reference

### Backend (.env location: `backend/.env`)
- MT5 credentials
- API keys (OpenAI, News API, etc.)
- Risk parameters
- Trading limits

### Frontend (.env location: `frontend/.env.local`)
- API URL (default: http://localhost:8000)
- WebSocket URL (default: ws://localhost:8000/ws)

---

**Happy Trading! 🤖📈**

Remember: This is a demo bot for educational purposes. Always test in demo mode first!
