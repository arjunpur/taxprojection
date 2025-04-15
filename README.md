# Tax Projection Dashboard

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd taxes-2025
   ```

2. Install dependencies using uv:
   ```
   uv pip install .
   ```
   
   Alternatively, uv will automatically use the dependencies defined in pyproject.toml.

## Running the Application

Use uv to run the Streamlit application:

```
uv tool run streamlit run tax_streamlit.py
```

The application will start and open in your default web browser. If it doesn't open automatically, navigate to http://localhost:8501.
