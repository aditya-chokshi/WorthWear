# Worthwear

Worthwear is an AI shopping companion for buying fewer, better products. It analyzes a product photo and scores durability, repairability, versatility, lifespan, and cost per use.

## Current features

- Upload JPG, JPEG, or PNG product photos
- Analyze products with Gemini vision
- Show a buy/skip recommendation with reasoning and an AI confidence caveat
- Save analyses and uploaded image paths to SQLite
- Review the Wardrobe Log with summary metrics and a cost-per-use chart

## Setup

Python 3.11 or newer is required.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add your Gemini API key before starting the app.
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`. Keep the terminal running while using it. Stop the server with `Ctrl+C`.

## Testing

Run the automated checks from the project root:

```powershell
python -m unittest discover -s tests -v
python -m py_compile app.py analyzer.py config.py db.py models.py
```

The automated tests use temporary SQLite files and mocked model responses, so they do not spend API quota. For a manual end-to-end check:

1. Start the app and upload a clear product photo.
2. Try one analysis with a price and one without a price.
3. Confirm the score card, recommendation, reasoning, and AI-estimate disclaimer appear.
4. Open `Wardrobe Log` and confirm the item, summary metrics, and chart appear.
5. Try an invalid price and confirm the app shows an error without crashing.

## Secrets and generated files

- Put the real key only in `.env`; never commit it.
- `.env`, `worthwear.db`, and `uploads/` are ignored by Git.
- Commit `.env.example` with placeholder values for other developers.

## GitHub workflow

After installing Git for Windows or GitHub Desktop, create an empty repository on GitHub named `worthwear`. From this folder, run:

```powershell
git init
git add .
git commit -m "Build Worthwear AI shopping companion"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/worthwear.git
git push -u origin main
```

For future work:

```powershell
git pull
git status
git add .
git commit -m "Describe the change"
git push
```

Use short feature branches for larger changes, run the tests before committing, and rotate the Gemini key immediately if it is ever exposed.
