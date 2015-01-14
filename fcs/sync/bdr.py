import json
from flask import current_app
import requests


def get_auth():
    return (
        current_app.config.get('BDR_ENDPOINT_USER', 'user'),
        current_app.config.get('BDR_ENDPOINT_PASSWORD', 'pass'),
    )


def do_bdr_request(params):
    url = get_absolute_url('/ReportekEngine/update_company_collection')
    auth = get_auth()
    ssl_verify = current_app.config['HTTPS_VERIFY']
    response = requests.get(url, params=params, auth=auth, verify=ssl_verify)

    error_message = ''
    if (response.status_code == 200 and
                response.headers.get('content_type') == 'application/json'):
        json_data = json.loads(response.contents)
        if json_data.get('status') != 'success':
            error_message = json_data.get('message')
    else:
        error_message = 'Invalid response'

    if error_message:
        current_app.logger.warning(error_message)

    return not error_message


def get_absolute_url(url):
    return current_app.config['BDR_ENDPOINT_URL'] + url
