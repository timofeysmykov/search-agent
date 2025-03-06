# AI Agent with Claude 3.5 Haiku and Perplexity

This project implements an AI agent that uses Claude 3.5 Haiku as the "brain" for processing and generating responses, and Perplexity as a search tool for retrieving up-to-date information from the internet.

## Features

- Command-line interface for interacting with the AI agent
- Integration with Claude 3.5 Haiku API for intelligent responses
- Integration with Perplexity API for web search capabilities
- Smart detection of when to use search functionality
- Modular architecture for easy extension and maintenance

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your API keys as environment variables:
   ```
   export CLAUDE_API_KEY="your_claude_api_key"
   export PERPLEXITY_API_KEY="your_perplexity_api_key"
   ```
   
   Alternatively, create a `.env` file in the project root with these variables.

3. Run the application:
   ```
   python main.py
   ```

## Project Structure

- `main.py`: Entry point for the application
- `llm_api.py`: Handles interaction with Claude 3.5 Haiku
- `search_api.py`: Manages Perplexity API calls for search functionality
- `utils.py`: Contains utility functions for data processing and formatting

## Usage

Simply run the application and enter your queries. The system will automatically determine when to use the search functionality based on your query.

Example queries:
- "What is the current weather in Moscow?"
- "What are the latest news about technology?"
- "Explain quantum computing"

## Web Interface (Optional)

The project includes an optional web interface built with Flask. To use it:

```
python web_app.py
```

Then open your browser and navigate to http://localhost:5000
