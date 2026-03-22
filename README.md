# Discord Scam Image Detector Bot

Discord bot that automatically detects scam images using perceptual hashing

## Features

- Automatic scam image detection in messages
- Hash comparison with configurable tolerance threshold
- Global and per-server database
- Automatic reports with action buttons
- Configurable automatic actions (delete, mute, kick, ban)
- Detection statistics tracking
- User notifications via DM
- False positives system
- Export/Import hashes

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Add your Discord token in `.env`:
```
DISCORD_TOKEN=your_token_here
```

4. Run the bot:
```bash
python bot.py
```

## Commands

`/help` - Display available commands

## Automatic Actions

- **none** - Report only, no action taken
- **delete** - Delete the message (default)
- **mute** - Delete message + mute user for 1 hour
- **kick** - Delete message + kick user
- **ban** - Delete message + ban user

## False Positives

If an image is incorrectly flagged:
1. Click the "False Positive" button in the report
2. The hash will be whitelisted for your server
3. Future messages with that image won't trigger detections
4. The button will change to "Mark as Scam" to allow reverting the decision

## Tolerance Threshold

The threshold determines detection sensitivity:
- 0 = Exact match only
- 5 = Recommended (tolerates compression, resizing)
- 10+ = More permissive (may generate false positives)


## Server Support

https://discord.gg/mgpHPAKWA2