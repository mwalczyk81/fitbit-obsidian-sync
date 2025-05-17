# 🦶 Fitbit Obsidian Sync

Automatically sync your daily Fitbit data (steps, calories, sleep) into your [Obsidian](https://obsidian.md) daily notes — no GUI, no extra plugins, just clean Markdown.

---

## ✨ Features

- ✅ Automatically pulls today’s Fitbit data via the API
- 🧠 Inserts data under `## 🧠 Health Summary` in your daily note
- 📆 Follows your Obsidian folder structure (e.g., `vault/2025/05-May/2025-05-17.md`)
- 🔁 Refreshes OAuth tokens without any manual work
- ⚙️ Can be run manually or automated with Task Scheduler / cron

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/fitbit-obsidian-sync.git
cd fitbit-obsidian-sync
```

### 2. Install dependencies with Poetry

```bash
poetry install
```

### 3. Set up your `.env` file

Create a `.env` file in the root of the repo:

```env
CLIENT_ID=your_fitbit_client_id
CLIENT_SECRET=your_fitbit_client_secret
VAULT_DIR=C:/Users/yourname/ObsidianVault/journal
```

### 4. Generate Fitbit tokens

Use this [Fitbit OAuth URL](https://dev.fitbit.com/build/reference/web-api/oauth2/authorization/) to authorize your app and exchange the code manually using `curl` or Python. Save the result as:

```
fitbit_tokens.json
```

Make sure it includes `access_token`, `refresh_token`, and `expires_at`.

---

## 🧠 Example Output

When you run the script:

```bash
poetry run python scripts/run_sync.py
```

It inserts into your daily note like:

```markdown
## 🧠 Health Summary

Sleep: 7.25 hrs  
Steps: 8,932  
Calories Burned: 2,043
```

If the section already exists, data is inserted or updated below `## 🧠 Health Summary`.

---

## 🛠 Project Structure

```
fitbit-obsidian-sync/
├── scripts/
│   └── run_sync.py         # CLI entrypoint
├── src/
│   └── fitbit_sync/
│       └── sync.py         # All the logic
├── .env
├── fitbit_tokens.json      # OAuth tokens
├── README.md
├── pyproject.toml
└── .gitignore
```

---

## ⏱ Automation

To run this every morning:

### Windows (Task Scheduler)

Use a scheduled task that runs:

```bash
poetry run python scripts/run_sync.py
```

### Linux/macOS (cron)

Add to your crontab:

```cron
0 7 * * * cd /path/to/repo && poetry run python scripts/run_sync.py
```

---

## 📋 License

MIT

---

## ❤️ Acknowledgments

- [python-fitbit](https://github.com/orcasgit/python-fitbit)
- [Obsidian](https://obsidian.md)
- You and your healthy habits
