# PikaBot
>Update time: 2025-05-16

LINE ID: @223myfde

---

## Environment
![Python Badge](https://img.shields.io/badge/Python-3.12.9-blue)

## Requirements
```bash
pip install -r requirements.txt
```

Create a file named `config.ini` in the root directory of your project and add the following content:

```ini
[LINE]
CHANNEL_ACCESS_TOKEN = <Your LINE Channel Access Token>
CHANNEL_SECRET = <Your LINE Channel Secret>

[GEMINI]
API_KEY = <Your Gemini API Key>

[SERVER]
PORT = 5000

[WEATHER]
CWB_API_KEY = <Your CWB (Central Weather Bureau) API Key>
```

### Description
- `[LINE]`: Credentials for your LINE Messaging API bot.
- `[GEMINI]`: API key for accessing Google Gemini.
- `[SERVER]`: The port number your Flask server will use (default is 5000).
- `[WEATHER]`: API key for Taiwan’s Central Weather Bureau weather data service.

Make sure to replace all placeholder values (`<...>`) with your actual credentials before running the application.

## Flowerchart
<img src="material/Bot%20flower.png" width="400"/>
<img src="material/Postman%20flower.png" width="400"/>



