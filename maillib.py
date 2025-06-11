import json
import string
import random
import requests
import time
from threading import Thread


class Listen:
    listen = False
    message_ids = []

    def message_list(self):
        url = "https://api.mail.tm/messages"
        headers = {'Authorization': 'Bearer ' + self.token}
        response = self.session.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return [
            msg for msg in data['hydra:member']
            if msg['id'] not in self.message_ids
        ]

    def message(self, idx):
        url = f"https://api.mail.tm/messages/{idx}"
        headers = {'Authorization': 'Bearer ' + self.token}
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def run(self):
        while self.listen:
            for message in self.message_list():
                self.message_ids.append(message['id'])
                message_data = self.message(message['id'])
                self.listener(message_data)
            time.sleep(self.interval)

    def start(self, listener, interval=3):
        if self.listen:
            self.stop()

        self.listener = listener
        self.interval = interval
        self.listen = True
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.listen = False
        if hasattr(self, 'thread'):
            self.thread.join()


def username_gen(length=24, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))


def password_gen(length=8, chars=string.ascii_letters + string.digits + string.punctuation):
    return ''.join(random.choice(chars) for _ in range(length))


class Email(Listen):
    token = ""
    domain = ""
    address = ""
    session = requests.Session()

    def __init__(self):
        if not self.domains():
            print("Failed to get domains")
    def domains(self):
        url = "https://api.mail.tm/domains"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        domains = []
        for domain in data['hydra:member']:
            if domain['isActive']:
                domains.append(domain['domain'])
        print(domains)
        if len(domains) >= 1:
            self.domain = random.choice(domains)
            return True

        return False
    def register(self, username=None, password=None, domain=None):
        self.domain = domain if domain else self.domain
        username = username if username else username_gen()
        password = password if password else password_gen()

        url = "https://api.mail.tm/accounts"
        payload = {
            "address": f"{username}@{self.domain}",
            "password": password
        }
        headers = {'Content-Type': 'application/json'}
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        self.address = data.get('address', f"{username}@{self.domain}")
        self.password = password
        self.acc_id = data["id"]
        self.get_token(password)

        if not self.address:
            raise Exception("Failed to create an address")
    def get_token(self, password):
        url = "https://api.mail.tm/token"
        payload = {
            "address": self.address,
            "password": password
        }
        headers = {'Content-Type': 'application/json'}
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        self.token = response.json().get('token')
        if not self.token:
            raise Exception("Failed to get token")
    def delete(self, render=True):
        try:
            if not self.acc_id or not self.token:
                raise Exception("Account ID or token is missing")
        except Exception:
            raise Exception("Account ID or token is missing")

        delete_url = f"https://api.mail.tm/accounts/{self.acc_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.session.delete(delete_url, headers=headers)
        if response.status_code == 204:
            if render:
                print("Account deleted successfully!")
        else:
            if render:
                print("Failed to delete account:", response.json())


if __name__ == "__main__":
    def listener(message):
        print("\nSubject:", message['subject'])
        content = message.get('text', message.get('html', ''))
        print("Content:", content)

    # Initialize Email and get domains
    test = Email()
    print("\nDomain:", test.domain)

    # Register new email address
    test.register()
    print("\nEmail Address:", test.address)

    try:
        # Start listening for new emails
        test.start(listener)
        print("\nWaiting for new emails...")

    except KeyboardInterrupt:
        # Stop listening and delete the account if interrupted
        test.delete()
        test.stop()

    # Stop listening and delete the account on completion
    test.delete()
    test.stop()


