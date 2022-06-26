import json
import requests
import boto3
import os

def lambda_handler(event, context):
  
  try:
    response = __collect_jira_data()  
    __write_to_s3(response)
  except Exception :
    return {
      "statusCode": 500
    }
  else :
    return {
      "statusCode": 200
    }

def __collect_jira_data() :
  jira_domain = os.getenv('JIRA_DOMAIN')
  jql_query = os.getenv('JQL_QUERY')
  url = 'https://' + jira_domain + '/rest/api/3/search'
  data = { 'jql': jql_query }

  session = requests.Session()
  api_secret = __get_api_secret()

  session.auth = (api_secret['user'], api_secret['api_token'])
  headers = {'Accept': 'application/json', 'Content-Type': 'application/json' }
  response = session.post(url, data=json.dumps(data), headers=headers)

  if response.status_code != 200:
    raise Exception('Could not get data from JIRA - status code: ' + response.status_code)

  return response

def __get_api_secret() :
  secret_name = os.getenv('API_TOKEN_SECRET_NAME')
  session = boto3.session.Session()
  client = session.client(service_name='secretsmanager')
  response = client.get_secret_value(SecretId=secret_name)

  if 'SecretString' in response:
    secret = json.loads(response['SecretString'])
    return secret

  raise Exception('Could not get api token from secrets manager')

def __write_to_s3(jira_response) :
  bucket_name = os.getenv('BUCKET_NAME')
  file_name = 'jira-sync.json'
  content_for_s3 = json.dumps(jira_response.json()['issues']).encode()

  s3 = boto3.client('s3')
  s3.put_object(Bucket=bucket_name, Key=file_name, Body=content_for_s3)