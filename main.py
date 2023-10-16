import time
from datetime import datetime
from dateutil import tz
import requests

from dotenv import load_dotenv
import os
import sib_api_v3_sdk as sendinblu

load_dotenv()


class Controller:
    def __init__(self):
        self.secret = os.environ.get('SOLAREDGE_API_KEY')
        self.site_id = os.environ.get('SOLAREDGE_SITE_ID')
        self.timezone = os.environ.get('TIMEZONE'); self.all_good = self.is_all_good()

    def _get_check_url(self):
        return f'https://monitoringapi.solaredge.com/site/{self.site_id}/overview?api_key={self.secret}'

    def is_all_good(self):
        r = requests.get(self._get_check_url()).json()
        hour = datetime.now(tz=tz.gettz(self.timezone)).hour
        should_not_be_night = 8 < hour < 17
        return not should_not_be_night or r['overview']['currentPower']['power'] > 0


class Notifier:
    def __init__(self):
        configuration = sendinblu.Configuration()
        configuration.api_key['api-key'] = os.environ.get('SENDINBLU')
        self.api_instance = sendinblu.TransactionalEmailsApi(sendinblu.ApiClient(configuration))
        self.counter = 0

    def send_email(self, subject, content, throttled=False):
        self.counter += 1
        if throttled:
            if self.counter % 24 != 0:
                return

        sender = {'email': 'monitor@solaredgemonitor.com'}
        to = {'email': os.environ.get('RECIPIENT_EMAIL')},
        text_content = content
        smtp_email = sendinblu.SendSmtpEmail(to=to, text_content=text_content, sender=sender, subject=subject)
        self.api_instance.send_transac_email(smtp_email)


if __name__ == '__main__':
    c = Controller()
    notifier = Notifier()
    print("Inizio controllo")
    while True:
        if not c.all_good:
            print(f"{datetime.now()} Errore impianto non attivo")
            notifier.send_email('Impianto non attivo!', 'Impianto non attivo!')
        else:
            print(f"{datetime.now()} Tutto ok")
            notifier.send_email('tutto ok', 'tutto ok', throttled=True)
        time.sleep(60 * 60)

