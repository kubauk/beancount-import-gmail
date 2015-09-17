import base64
from datetime import timedelta
import email
import os

from googleapiclient import discovery
import httplib2
from oauth2client import client
from oauth2client import tools
import oauth2client
from oauth2client.file import Storage


SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'PayPal Quickened'


class Retriever:
    _current_service = None
    _email_cache = dict()

    def __init__(self, args, email_address):
        super().__init__()
        self._args = args
        self._email_address = email_address

    def get_messages_for_date(self, transaction_date):
        return self._email_cache.get(transaction_date, self._retrieve_messages(transaction_date))

    def _get_service(self):
        if self._current_service is None:
            self._current_service = self._build_service(self._get_credentials())
        return self._current_service

    def _get_credentials(self):
        store = oauth2client.file.Storage(os.path.join(".", "credentials.json"))
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        return tools.run_flow(flow, store, self._args)

    def _list_messages_for_day(self, transaction_date):
        service = self._get_service()
        after = transaction_date.strftime("%Y/%m/%d")
        before = (transaction_date + timedelta(days=1)).strftime("%Y/%m/%d")
        query = 'from:service@paypal.co.uk after:%s before:%s' % (after, before)
        list_request = service.users().messages().list(userId=self._email_address, q=query)
        result = list_request.execute()
        messages = result.get('messages', [])
        return messages

    def _retrieve_messages(self, transaction_date):
        message_ids = self._list_messages_for_day(transaction_date)
        messages = list()
        for message_id in message_ids:
            messages.append(self._get_message(message_id))
        return messages

    def _get_message(self, message_id):
        service = self._get_service()
        get_query = service.users().messages().get(userId=self._email_address, id=message_id['id'], format='raw')
        result = get_query.execute()

        message_bytes = base64.urlsafe_b64decode(result['raw'].encode('ASCII'))
        return email.message_from_string(message_bytes.decode('ascii'))

    # @staticmethod
    # def _parse_part(part):
    # mime_type = part['mimeType']
    #     content_type = list(filter(lambda header: header['name'] == 'Content-Type', part['headers'])).pop()
    #     if content_type is None:
    #         raise Exception()
    #
    #     if mime_type == "text/html":
    #         pass
    #     elif mime_type == "text/plain":
    #         pass

    @staticmethod
    def _build_service(current_credentials):
        http = current_credentials.authorize(httplib2.Http())
        return discovery.build('gmail', 'v1', http=http)
