#!/usr/bin/python3

import os
import re

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

CLIENT_SECRETS_FILE = 'client_secret.json'

SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Аутентификация в два аккаунта с созданием локального веб-сервера на 2х разных портах
def get_authenticated_service(export: bool):
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  if export:
    credentials = flow.run_local_server(port=8080, prompt='consent')
  else:
    credentials = flow.run_local_server(port=8081, prompt='consent')
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

# Получение имени текущего канала для проверки
def get_current_channel_name(service):
  try:
    response = service.channels().list(part="snippet", mine=True).execute()
    if response.get('items'):
      return response['items'][0]['snippet']['title']
  except Exception as e:
      print(f"{bcolors.WARNING}Note: Could not retrieve channel name: {e}{bcolors.ENDC}")
  return "Unknown"

# Вызов API youtube.subscriptions.list для постраничной выгрузки подписок
def get_channel_ids(service, target_channels):
  next_page_token = ''
  while True:
    response = service.subscriptions().list(
      part="snippet",
      mine=True,
      maxResults=50,
      pageToken=next_page_token
    ).execute()
    for item in response.get('items', []):
      target_channels.append(item['snippet']['resourceId']['channelId'])
    
    next_page_token = response.get('nextPageToken')
    if not next_page_token:
      break

# Вызов API youtube.subscriptions.insert для добавления подписки на канал
def add_subscription(youtube, channel_id):
  add_subscription_response = youtube.subscriptions().insert(
    part='snippet',
    body=dict(
      snippet=dict(
        resourceId=dict(
          channelId=channel_id
        )
      )
    )).execute()
  return add_subscription_response


if __name__ == '__main__':

  print()
  print(bcolors.WARNING + 'Login to Google-account for export!' + bcolors.ENDC)
  print()

  youtube_export = get_authenticated_service(export=True)
  export_name = get_current_channel_name(youtube_export)
  print(f"Logged in as (Export): {bcolors.OKGREEN}{export_name}{bcolors.ENDC}")

  export_account_channels = []
  get_channel_ids(youtube_export, export_account_channels)
  print(f"Found {len(export_account_channels)} subscriptions in Export account.")

  print(f"\n{bcolors.WARNING}--- EXPORT COMPLETE ---{bcolors.ENDC}")
  input(f"Press {bcolors.OKGREEN}Enter{bcolors.ENDC} to proceed to the IMPORT account login...")

  print()
  print(bcolors.WARNING + 'Login to Google-account for import!' + bcolors.ENDC)
  print()

  youtube_import = get_authenticated_service(export=False)
  import_name = get_current_channel_name(youtube_import)
  print(f"Logged in as (Import): {bcolors.OKGREEN}{import_name}{bcolors.ENDC}")

  import_account_channels = []
  get_channel_ids(youtube_import, import_account_channels)
  print(f"Found {len(import_account_channels)} subscriptions in Import account.")

  # Use set difference (export - import) to find channels in export that are NOT in import
  channels_to_add = list(set(export_account_channels) - set(import_account_channels)) 
  channels_to_add_quantity = len(channels_to_add)

  print(f"\n{bcolors.BOLD}SYNC ANALYSIS:{bcolors.ENDC}")
  print(f"Export Account Total: {len(export_account_channels)}")
  print(f"Import Account Total: {len(import_account_channels)}")
  print(f"New channels to add: {bcolors.OKGREEN}{channels_to_add_quantity}{bcolors.ENDC}")

  if channels_to_add_quantity == 0:
    print(f"\n{bcolors.OKGREEN}Accounts are already in sync! No actions needed.{bcolors.ENDC}")
    quit()
  
  if channels_to_add_quantity > 180:
      print(f"\n{bcolors.WARNING}WARNING: You are about to add {channels_to_add_quantity} subscriptions.{bcolors.ENDC}")
      print("This is close to or exceeds the daily API limit (~200).")
      print("The script will stop automatically if the limit is reached.")

  confirm = input(f"\nDo you want to proceed with adding {channels_to_add_quantity} subscriptions? (y/n): ")
  if confirm.lower() != 'y':
      print("Operation cancelled by user.")
      quit()

  print()
  counter = 0
  try:
    for channel_id in channels_to_add:
      add_subscription(youtube_import, channel_id)
      counter += 1
  except HttpError as e:
    print()
    print(bcolors.FAIL + 'An HTTP error {} occurred:\n{}'.format(e.resp.status, e.content) + bcolors.ENDC)
    print()
    print('A subscriptions to ' + str(counter) + ' channels ' + 'was ' + bcolors.OKGREEN + 'added.' + bcolors.ENDC)
  else:
    print()
    print('A subscriptions to ' + str(counter) + ' channels ' + 'was ' + bcolors.OKGREEN + 'added.' + bcolors.ENDC)
