# Azure AI Foundry WhatsApp Bot

A production-ready WhatsApp bot implementation using Azure Functions, Azure OpenAI, and WhatsApp Business API.

## Features

- Voice message transcription
- Azure OpenAI integration
- WhatsApp Business API webhook handling
- Secure configuration management
- Production-ready error handling

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your values
3. Deploy to Azure Functions

## Configuration

Required environment variables:

```
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=
PHONE_NUMBER_ID=
ACCESS_TOKEN=
VERIFY_TOKEN=
RECIPIENT_WAID=
```

## Security

- All sensitive information must be stored in environment variables
- Never commit `.env` files
- Use managed identities where possible
- Rotate access tokens regularly

## License

MIT