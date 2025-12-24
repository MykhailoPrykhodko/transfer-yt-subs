#!/usr/bin/python3
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Colors for output
class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Аутентификация
def get_authenticated_service():
  if not os.path.exists(CLIENT_SECRETS_FILE):
    print(f"{bcolors.FAIL}Error: '{CLIENT_SECRETS_FILE}' not found.{bcolors.ENDC}")
    return None

  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_local_server(port=8080)
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def list_subscriptions(service):
    subscriptions = []
    next_page_token = ''
    
    print(f"\n{bcolors.WARNING}Fetching subscriptions...{bcolors.ENDC}")
    
    while True:
        request = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response.get('items', []):
            sub_title = item['snippet']['title']
            channel_id = item['snippet']['resourceId']['channelId']
            subscriptions.append({'title': sub_title, 'id': channel_id})

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
            
    return subscriptions

def main():
    print(f"{bcolors.BOLD}--- YouTube Subscription Checker ---{bcolors.ENDC}")
    print("This script will list all subscriptions for the logged-in account.")
    print("Please log in when the browser window opens.")
    
    service = get_authenticated_service()
    if not service:
        return

    try:
        # Get channel info to show WHO is logged in
        channel_info = service.channels().list(part="snippet", mine=True).execute()
        if channel_info.get('items'):
            my_channel_title = channel_info['items'][0]['snippet']['title']
            print(f"\nLogged in as: {bcolors.OKGREEN}{my_channel_title}{bcolors.ENDC}")
        
        subs = list_subscriptions(service)
        
        print(f"\nTotal Subscriptions found: {bcolors.OKGREEN}{len(subs)}{bcolors.ENDC}")
        
        if len(subs) > 0:
            print("\nFirst 10 subscriptions:")
            for i, sub in enumerate(subs[:10], 1):
                print(f"{i}. {sub['title']}")
            
            if len(subs) > 10:
                print(f"... and {len(subs) - 10} more.")
        else:
            print(f"\n{bcolors.WARNING}No subscriptions found!{bcolors.ENDC}")
            print("Possible reasons:")
            print("1. You logged into the wrong Google Account.")
            print("2. You have a Brand Account. Make sure to select the specific BRAND ACCOUNT icon in the login screen, not your email.")

    except Exception as e:
        print(f"\n{bcolors.FAIL}An error occurred:{bcolors.ENDC} {e}")

if __name__ == '__main__':
    main()
