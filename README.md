# LLM Chat with Tabular Data

## Quick Start

### Initial State

1. Set up environment
2. Configure LLM sources
3. Load data into local database


#### Environment

Install [uv](https://docs.astral.sh/uv/) as per user preference.

#### LLM Sources

Either configure [Ollama](https://ollama.com/) locally and download a model of choosing (eg gemma3:30b) or populate [OpenAI API keys](https://platform.openai.com/api-keys) for one of their models.

#### Local Data

Download desired data sets. Data Sources for Monthly Prescription Drug Plan Formulary and Pharmacy Network Information can be found [here](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/monthly-prescription-drug-plan-formulary-and-pharmacy-network-information).

Place the zip files as desired (in `./data/` for example) and then run `read_data.py` to populate the local duckdb database. Load as many zips as desired into the database (NOTE: no protection against duplicate data from running more than once).

```bash
uv run python read_data.py --zip-path data/monthly.zip
```

This will populate the `database.db` for the main chat application.

### Start

Run the chat locally via:

```bash
uv run streamlit run main.py
```

The default browser will open (after accepting or rejecting streamlit terms) with the chat interface.

![](data/screenshot.png)

## Dev

Formatting and linting are here. Testing is not presently included.

```bash
uv run black .
uv run ruff check . --fix
```