# Pretty-Good-AI-Voice-Bot

## Overview

This repository contains a Flask-based voice bot (`bot.py`) that uses SignalWire, and the OpenAI API to simulate patient calls to a medical office. The bot responds to different scenarios and logs transcripts and bug reports. This README explains how to run the code on a personal machine.

---

## Prerequisites

- **Python** 3.10 or newer
- **ngrok** (for exposing the local Flask server to the internet)
- A **SignalWire** account with Project ID, Auth Token, and Space URL
- A **SignalWire phone number** configured for outbound calls
- **OpenAI API key** (with chat/completions access)
- A `prettyGood.env` file in the project root with required environment variables (see below)

---

## Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd Pretty-Good-AI-Voice-Bot
   ```

2. **Install Python dependencies**

   ```bash
   pip install flask python-dotenv signalwire twilio openai
   ```

   You may install these globally or with whatever package manager you prefer; a virtual environment is *not required* for this project.


4. **Create the environment file** (`prettyGood.env`) in the project root with the following keys:
   ```text
   SIGNALWIRE_PROJECT_ID=your_project_id
   SIGNALWIRE_AUTH_TOKEN=your_auth_token
   SIGNALWIRE_SPACE_URL=your_space.signalwire.com
   SIGNALWIRE_PHONE_NUMBER=+1XXXXXXXXXX   # your SignalWire phone number
   TARGET_PHONE_NUMBER=+1YYYYYYYYYY       # number you want the bot to call
   OPENAI_API_KEY=sk-...
   ```
   Adjust values to match your account details. `bot.py` loads this file at startup.

---

## Running the Bot

1. **Start the Flask server**

   ```bash
   python bot.py
   ```

   By default the app listens on port `5000` (`http://127.0.0.1:5000`).

2. **Expose the server with ngrok**
   - Download/install ngrok from https://ngrok.com/
   - Run the following in a separate terminal:
     ```bash
     ngrok http 5000
     ```
   - Copy the generated HTTPS forwarding URL (e.g. `https://abcd1234.ngrok.io`).

3. **Trigger a call via the `/call` endpoint**
   SignalWire needs a publicly accessible URL for webhooks, so use the ngrok URL. Replace `<ngrok-url>` with the one from step 2.

   ```bash
   curl "<ngrok-url>/call?scenario=schedule_appointment"
   ```

   Valid scenarios correspond to Flask routes defined in `bot.py` (e.g. `schedule_appointment`, `reschedule_appointment`, `cancel_appointment`, etc.).

   The bot will initiate a call to the `TARGET_PHONE_NUMBER` using the `SIGNALWIRE_PHONE_NUMBER` defined in the `.env` file.

---

## Notes

- Transcripts for each scenario are saved in files named `transcript_*.txt`. They are cleared when the `/call` endpoint is hit.
- After each call, `bugs.txt` will contain any high‑impact issues identified by the OpenAI model.
- If you change the Flask port, update the `ngrok http` command accordingly (e.g. `ngrok http 8000`).

---
