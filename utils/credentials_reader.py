import boto3
import json


class CredentialsReader(object):
    def __init__(self, secret_name: str):
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(
            SecretId=secret_name
        )

        if 'SecretString' in response:
            db_credential = json.loads(response["SecretString"])
            self._username = db_credential['username']
            self._password = db_credential['password']
        else:
            raise Exception("No SecretString")

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

