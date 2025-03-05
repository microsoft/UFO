# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import smtplib
import threading
from concurrent.futures import ThreadPoolExecutor
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from multiprocessing.pool import ThreadPool
from typing import List

from tqdm import tqdm

from ufo.config.config import Config
from ufo.module.basic import BaseSession
from ufo.utils.azure_storage import AzureBlobStorage

_configs = Config.get_instance().config_data

class UFOClientManager:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self._session_list = session_list

    def run_all(self) -> None:
        """
        Run the batch UFO client.
        """
        blob_storage = None
        if _configs["UPLOAD"]:
            blob_storage = AzureBlobStorage()

        total = len(self.session_list)

        with ThreadPoolExecutor(max_workers=16) as executor:
            for idx, session in enumerate(tqdm(self.session_list), start=1):
                session.run()

                if _configs["MONITOR"]:
                    send_point = _configs["SEND_POINT"].split(",")
                    if str(idx) in send_point:
                        message = f"Ufo Execute Completed: {idx}/{total}"
                        send_message(message)

                if _configs["UPLOAD"]:
                    executor.submit(lambda : blob_storage.upload_folder(session.log_path, _configs["DATA_SOURCE"]))


    @property
    def session_list(self) -> List[BaseSession]:
        """
        Get the session list.
        :return: The session list.
        """
        return self._session_list

    def add_session(self, session: BaseSession) -> None:
        """
        Add a session to the session list.
        :param session: The session to add.
        """
        self._session_list.append(session)

    def next_session(self) -> BaseSession:
        """
        Get the next session.
        :return: The next session.
        """
        return self._session_list.pop(0)

def send_message(message: str) -> None:
    """
    Send a message.
    :param message: message to send.
    """
    # email info
    sender_email = _configs["FROM_EMAIL"]
    sender_password = _configs["SENDER_PASSWORD"]
    receiver_email = _configs["TO_EMAIL"]
    server_host = _configs["SMTP_SERVER"]
    machine_id = _configs["MACHINE_ID"]

    msg = MIMEMultipart()
    msg["From"] = _configs["FROM_EMAIL"]
    msg["TO"] = _configs["TO_EMAIL"]
    msg["Subject"] = Header(f"Execute Reminder: {machine_id}")
    msg.attach(MIMEText(message, "plain", 'utf-8'))

    server = None
    try:
        # Connect SMTP Server
        server = smtplib.SMTP(server_host, 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # send email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Send Email to {receiver_email} sucessfully.")
    except Exception as e:
        print(f"Send Email to {receiver_email} failed: {e}.")
    finally:
        try:
            if server:
                server.quit()
        except Exception:
            return
