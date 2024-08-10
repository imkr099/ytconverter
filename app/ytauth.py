# from google.oauth2 import service_account
# from googleapiclient.discovery import build
#
# SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
# SERVICE_ACCOUNT_FILE = 'C:/tgprojects/ytconverter/solar-cab-432112-t4-e10a23ae581c.json'
#
# credentials = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#
# youtube = build('youtube', 'v3', credentials=credentials)
#
# request = youtube.channels().list(
#     part='snippet,contentDetails,statistics',
#     mine=True
# )
# response = request.execute()
