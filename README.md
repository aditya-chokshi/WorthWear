# Worthwear

> An AI shopping companion for buying fewer, better products.

Worthwear analyzes a product photo and helps you decide whether it is worth buying. It estimates durability, repairability, versatility, lifespan, and cost per use, then gives a transparent **buy** or **skip** recommendation.

## What It Does

- Accepts JPG, JPEG, and PNG product photos
- Uses Gemini vision to analyze the visible product
- Scores durability, repairability, and versatility from 1 to 10
- Estimates material and useful lifespan
- Calculates estimated cost per use when a price is supplied
- Explains the recommendation in plain language
- Clearly labels results as AI estimates, not verified facts
- Saves completed analyses to SQLite
- Provides a Wardrobe Log with history, summary metrics, and a cost-per-use chart

## Demo Gallery

Public sample products are stored in [`Images/`](Images/). These files are useful for manual testing and demonstrations.

Additional public or consented test photos can be placed in [`test_images/`](test_images/). Do not put private, identifying, or copyrighted images in the repository without permission.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Interface | Streamlit |
| Vision analysis | Google Gemini API |
| Persistence | SQLite via Python `sqlite3` |
| Image handling | Pillow |
| Configuration | `python-dotenv` |
| Tests | Python `unittest` |

## Project Structure

```text
worthwear/
├── app.py                 # Streamlit interface and user workflow
├── analyzer.py            # Gemini prompt, API call, parsing, and errors
├── config.py              # Environment variables and model selection
├── db.py                  # SQLite schema, storage, history, and statistics
├── models.py              # ProductAnalysis dataclass and validation
├── tests/
│   └── test_core.py       # Model and database tests
├── Images/                # Committed demo images
├── test_images/           # Optional committed test images
├── .env.example           # Safe configuration template
├── requirements.txt       # Python dependencies
└── worthwear.db           # Runtime database, created locally and ignored
```

## Requirements

- Python 3.11 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- Git, if you want to contribute or push changes to GitHub

## Local Setup

From the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and add your real key:

```env
GEMINI_API_KEY=your_actual_key_here
```

Never commit `.env` or share its contents. The application currently uses the Gemini model configured in `config.py`.

## Run the App

```powershell
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. Keep the terminal running while using the app. Stop the server with `Ctrl+C`.

### Analyze a product

1. Open the **Analyze** tab.
2. Upload a clear product photo.
3. Optionally enter the product name and price.
4. Click **Analyze**.
5. Review the score card, recommendation, reasoning, and confidence note.

### Review your history

Open **Wardrobe Log** to see saved analyses, total items, average cost per use, buy-versus-skip counts, and the cost-per-use trend.

## Testing

Run the automated tests from the project root:

```powershell
python -m unittest discover -s tests -v
python -m py_compile app.py analyzer.py config.py db.py models.py
```

The automated tests use temporary SQLite databases and do not call Gemini, so they do not consume API quota. For a manual test, use one of the files in `Images/`, try both a priced and unpriced analysis, open the Wardrobe Log, and test an invalid price such as `abc`.

## Data and Privacy

- `.env` contains your secret Gemini API key and is ignored by Git.
- `worthwear.db` contains local analysis history and is ignored by Git.
- `uploads/` contains runtime-uploaded images and is ignored by Git.
- `Images/` and `test_images/` are intended for public, non-sensitive demo assets only.
- Gemini results are estimates based on visual evidence and should not be treated as verified product claims.
- Do not upload private photos, personal information, or images you do not have permission to redistribute.

## GitHub Workflow

The repository is available at [github.com/aditya-chokshi/WorthWear](https://github.com/aditya-chokshi/WorthWear).

After changing code:

```powershell
git pull
python -m unittest discover -s tests -v
git status
git add .
git commit -m "Describe the change"
git push
```

Before committing, confirm that `.env`, `worthwear.db`, and `uploads/` are not listed by `git status`.

For larger changes, use a feature branch:

```powershell
git switch -c feature/short-description
# make and test your changes
git add .
git commit -m "Describe the feature"
git push -u origin feature/short-description
```

If an API key is ever exposed, revoke it immediately in Google AI Studio, create a replacement, update `.env`, and restart the app.

## License

No license has been selected yet. Add a license before accepting external contributions or redistributing the project.
