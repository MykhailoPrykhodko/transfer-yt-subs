#!/usr/bin/python3
import os
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/youtube']  # Full access needed for playlists
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service(export: bool):
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    if export:
        # Use prompt='consent' to ensure we get a refresh token and a clean session
        credentials = flow.run_local_server(port=8080, prompt='consent')
    else:
        credentials = flow.run_local_server(port=8081, prompt='consent')
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_current_channel_name(service):
    try:
        response = service.channels().list(part="snippet", mine=True).execute()
        if response.get('items'):
            return response['items'][0]['snippet']['title']
    except Exception as e:
        print(f"{bcolors.WARNING}Note: Could not retrieve channel name: {e}{bcolors.ENDC}")
    return "Unknown"

def get_playlists(service):
    """Fetches all playlists (ID, Title, Description) from the account."""
    playlists = []
    next_page_token = ''
    while True:
        request = service.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response.get('items', []):
            playlists.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description']
            })

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return playlists

def get_playlist_items(service, playlist_id):
    """Fetches all video IDs from a specific playlist."""
    video_ids = []
    next_page_token = ''
    while True:
        try:
            request = service.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get('items', []):
                # Retrieve the video ID. Note: It might be resourceId['videoId']
                resource = item['snippet'].get('resourceId')
                if resource and resource.get('kind') == 'youtube#video':
                     video_ids.append(resource['videoId'])

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as e:
            print(f"{bcolors.FAIL}Error reading playlist items: {e}{bcolors.ENDC}")
            break
            
    return video_ids

def create_playlist(service, title, description):
    """Creates a new playlist and returns its ID."""
    try:
        response = service.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": "private"  # Default to private for safety
                }
            }
        ).execute()
        return response['id']
    except HttpError as e:
        print(f"{bcolors.FAIL}Error creating playlist '{title}': {e}{bcolors.ENDC}")
        return None

def add_video_to_playlist(service, playlist_id, video_id):
    """Adds a video to a playlist."""
    try:
        service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        return True
    except HttpError as e:
        # 409 usually means the video is already in the playlist or duplicate
        if e.resp.status == 409:
             print(f"Video {video_id} already exists in playlist.")
        elif e.resp.status == 404:
             print(f"Video {video_id} not found (might be deleted/private).")
        else:
            print(f"{bcolors.FAIL}Error adding video {video_id}: {e}{bcolors.ENDC}")
        return False

def main():
    print(f"{bcolors.BOLD}--- YouTube Playlist Migrator ---{bcolors.ENDC}")
    print("NOTE: This script consumes HIGH API QUOTA.")
    print("Daily Quota is usually 10,000 units.")
    print("Creating a playlist = 50 units. Adding 1 video = 50 units.")
    print("Roughly max ~190 videos can be migrated per day.")
    
    # --- Step 1: Export ---
    print(f"\n{bcolors.WARNING}Login to Google-account for EXPORT!{bcolors.ENDC}")
    service_export = get_authenticated_service(export=True)
    export_name = get_current_channel_name(service_export)
    print(f"Logged in as (Export): {bcolors.OKGREEN}{export_name}{bcolors.ENDC}")

    print("Fetching playlists from export account...")
    export_playlists = get_playlists(service_export)
    print(f"Found {len(export_playlists)} playlists.")
    
    if not export_playlists:
        print("No playlists found to export.")
        return

    # Let user choose playlists (optional, simplified for now: migrate all or specific index)
    print("\nAvailable Playlists:")
    for idx, pl in enumerate(export_playlists):
        print(f"{idx + 1}. {pl['title']} (ID: {pl['id']})")

    # Ask user which playlists to migrate
    selection = input(f"\nEnter the numbers of playlists to migrate (comma separated, e.g. 1,3) or 'all': ")
    
    selected_playlists = []
    if selection.lower().strip() == 'all':
        selected_playlists = export_playlists
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            for i in indices:
                if 0 <= i < len(export_playlists):
                    selected_playlists.append(export_playlists[i])
        except ValueError:
            print(f"{bcolors.FAIL}Invalid input.{bcolors.ENDC}")
            return

    if not selected_playlists:
        print("No valid playlists selected.")
        return

    print(f"\nSelected {len(selected_playlists)} playlists to migrate.")

    print(f"\n{bcolors.WARNING}--- EXPORT PREPARATION COMPLETE ---{bcolors.ENDC}")
    input(f"Press {bcolors.OKGREEN}Enter{bcolors.ENDC} to proceed to the IMPORT account login...")

    # --- Step 2: Import ---
    print(f"\n{bcolors.WARNING}Login to Google-account for IMPORT!{bcolors.ENDC}")
    service_import = get_authenticated_service(export=False)
    import_name = get_current_channel_name(service_import)
    print(f"Logged in as (Import): {bcolors.OKGREEN}{import_name}{bcolors.ENDC}")

    if import_name == "Unknown":
        print(f"{bcolors.FAIL}Critical Error: Failed to authenticate Import account correctly. Aborting to save quota.{bcolors.ENDC}")
        return

    # --- Step 3: Migration Loop ---
    total_videos_migrated = 0
    quota_warning_shown = False

    for pl in selected_playlists:
        print(f"\nProcessing Playlist: {bcolors.BOLD}{pl['title']}{bcolors.ENDC}")
        
        # Get videos from source
        video_ids = get_playlist_items(service_export, pl['id'])
        print(f"  - Found {len(video_ids)} videos.")

        if not video_ids:
            continue

        # Create new playlist on destination
        print(f"  - Creating playlist '{pl['title']}' on import account...")
        new_playlist_id = create_playlist(service_import, pl['title'], pl['description'])
        
        if not new_playlist_id:
            print("  - Failed to create playlist. Skipping...")
            continue

        # Add videos
        print(f"  - Migrating videos (this may take time)...")
        count = 0
        for vid in video_ids:
            success = add_video_to_playlist(service_import, new_playlist_id, vid)
            if success:
                count += 1
                total_videos_migrated += 1
                # Small sleep to be gentle? Not strictly necessary for quota but good for stability
                # time.sleep(0.5) 
            
            # Simple check to warn user about quota limits approximately
            if total_videos_migrated > 190 and not quota_warning_shown:
                 print(f"\n{bcolors.FAIL}WARNING: You are approaching the daily API quota limit (~200 writes).{bcolors.ENDC}")
                 print("If the script crashes with 'quotaExceeded', please wait 24 hours.")
                 quota_warning_shown = True

        print(f"  - Done. Migrated {count}/{len(video_ids)} videos.")

    print(f"\n{bcolors.OKGREEN}Migration Complete! Total videos migrated: {total_videos_migrated}{bcolors.ENDC}")

if __name__ == '__main__':
    main()
