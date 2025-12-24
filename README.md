# YouTube Transfer Tools

A collection of Python scripts to migrate your YouTube data (Subscriptions and Playlists) from one Google account to another.

## Features

*   **Transfer Subscriptions:** Move all your channel subscriptions from Account A to Account B.
*   **Smart Sync:** Logic to only add *missing* subscriptions. If you run it again, it acts as a sync tool without duplicating or wasting quota.
*   **Transfer Playlists:** Migrate your playlists and the videos inside them.
*   **Diagnostics:** Check which account/channel your script is actually seeing to debug "zero subscriptions" issues.
*   **Safety Checks:** Built-in pauses and confirmation prompts to prevent accidental API quota exhaustion.

## Prerequisites

1.  **Python 3** installed.
2.  A **Google Cloud Project** with the YouTube Data API v3 enabled.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd transfer-yt-subs
    ```

2.  Install dependencies:
    ```bash
    pip install -r req.txt
    ```

## Google API Setup (Required)

To use these scripts, you must create your own "App" in the Google Cloud Console.

1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  **Create a Project** (or select an existing one).
3.  **Enable API:**
    *   Go to **APIs & Services** > **Library**.
    *   Search for "YouTube Data API v3".
    *   Click **Enable**.
4.  **Configure Consent Screen:**
    *   Go to **APIs & Services** > **OAuth consent screen**.
    *   Select **External** user type.
    *   Fill in the required fields (App name, support email, developer contact info).
    *   **IMPORTANT:** Under **Test users**, click **+ ADD USERS**. Add **BOTH** email addresses you intend to use (the Export account and the Import account). If you skip this, you will get a "403 Access Denied" error.
    *   Save and continue.
5.  **Create Credentials:**
    *   Go to **APIs & Services** > **Credentials**.
    *   Click **Create Credentials** > **OAuth client ID**.
    *   Application type: **Desktop app** (or "Web application").
    *   If you choose "Web application", add these to **Authorized redirect URIs**:
        *   `http://localhost:8080/`
        *   `http://localhost:8081/`
    *   Click **Create**.
    *   Download the JSON file, rename it to `client_secret.json`, and place it in the project folder.

## Usage

### 1. Transfer Subscriptions
This script transfers channel subscriptions. It calculates the difference between accounts and only adds what is missing.

```bash
python transfer-yt-subs.py
```

*   **Step 1:** Log in to the **Source** account (Export).
*   **Step 2:** The script will verify the channel name and count subscriptions.
*   **Step 3:** Press Enter to proceed.
*   **Step 4:** Log in to the **Target** account (Import). **Note:** Ensure you select the correct Brand Account if prompted.
*   **Step 5:** Review the summary. If you are adding >180 channels, the script will warn you about quota limits. Confirm to start.

### 2. Transfer Playlists
This script recreates your playlists on the new account and adds videos to them.

```bash
python transfer_playlists.py
```

*   **Warning:** This consumes high API quota (50 units per video). You can transfer ~190 videos per day.
*   Follow the on-screen prompts to select which playlists to migrate.

### 3. Check Subscriptions (Debug)
Use this if the transfer script says "Found 0 subscriptions". It helps verify which identity the script is logging into.

```bash
python check_subs.py
```

## Quota Limitations

The YouTube Data API has a default daily quota of **10,000 units**.
*   **Read (List):** 1 unit.
*   **Write (Subscribe/Playlist Item):** 50 units.

This means you can perform roughly **200 write operations** (subscriptions or playlist video adds) per day.
*   **Subscriptions:** If you have 1000 subs, it will take ~5 days to transfer them all. The script will stop automatically when the limit is reached. You can run it again the next day to continue where it left off.
*   **Playlists:** Similarly, large playlists will take multiple days to migrate.

## Troubleshooting

*   **Error 403 (Access Denied):** You forgot to add your email to the "Test users" list in Google Cloud Console.
*   **Found 0 Subscriptions:** You likely logged into the main Google Account email instead of the specific **Brand Account** that holds your data. Use `python check_subs.py` to verify your identity.
*   **Quota Exceeded:** You hit the 10,000 unit daily limit. Wait 24 hours (quota resets at Midnight Pacific Time) and run the script again.

## License

Licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).