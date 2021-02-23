#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import logging
import time
import requests
from requests.exceptions import HTTPError
import subprocess
import sys
import urllib

from utils.constants import TELEGRAM_URL, TELEGRAM_HOST, TELEGRAM_PORT
from utils.os_cmds import NC_CMD

logging.basicConfig(level=logging.INFO)
class_logger = logging.getLogger('wlanpi-bot-comms')

class TelegramComms(object):

    """
    Class to send alert messages to Telegram Bot 

    Arguments:
        api_key {mandatory str} -- [API token string from Telegram Bot]
    
    Usage:
        api_key = 1283738991:AAHe9eHOP_uCe6773bWjQTNvHT_lKyeGeew"
        sender = MessageBot(api_key)
        messages = ['Hello World!', 'This is the next line']

        if not sender.send_msg(messages):
            print(f"Send failed: {sender.err_msg}")
    
    """

    def __init__(self, api_key):

        self.api_key = api_key
        self.chat_id = False
        self.err_msg = ''
        self.long_polling_timeout = 100
        self.bot_url = "{}/bot{}/".format(TELEGRAM_URL, self.api_key)

    def send_msg(self, messages, chat_id):

        """
        Method to send messages to Telegram Bot 

        Arguments:
            messages {mandatory list/str} -- [list of messages or single string  to be sent to bot]
        
        Returns:
            On failure : False (error message in self.err_msg)
            Sucess: True

        """
        # make sure chat_id available from this object
        if not self.chat_id:
            self.chat_id = chat_id
      
        message = ''
        if isinstance(messages, str):
            message =  messages
        else:
            for line in messages:
                message += line  + "\n"        

        # correctly encode message
        message = urllib.parse.quote_plus(message)
        url = f"{TELEGRAM_URL}/bot{self.api_key}/sendMessage?chat_id={chat_id}&parse_mode=html&text={message}"

        try:
            requests.post(url)
        except HTTPError as http_err:
            self.err_msg = f'HTTP error occurred: {http_err}'
            class_logger.error(self.err_msg)
            return False
        except Exception as err:
            self.err_msg = f'Other error occurred: {err}'
            class_logger.error(self.err_msg)
            return False
        
        return True
    

    def get_url(self, url):
        
        try:
            response = requests.get(url)
        except HTTPError as http_err:
            self.err_msg = f'HTTP error occurred: {http_err}'
            class_logger.error(self.err_msg)
            return False
        except Exception as err:
            self.err_msg = f'Other error occurred: {err}'
            class_logger.error(self.err_msg)
            return False
        
        content = response.content.decode("utf8")
        return content


    def get_json_from_url(self, url):

        content = self.get_url(url)

        if content:
            js = json.loads(content)
            return js
        else:
            return False


    def get_updates(self, offset=None):
        url =  "{}getUpdates?timeout={}".format(self.bot_url, self.long_polling_timeout)
        
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        
        if js:
            return js
        else:
            return False


    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)


    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    def check_api_access(self):
        try:
            subprocess.check_output('{} -zvw10 {} {}'.format(NC_CMD, TELEGRAM_HOST, TELEGRAM_PORT), stderr=subprocess.STDOUT, shell=True).decode()
            class_logger.debug("  Port connection to {}, port: {} checked OK.".format(TELEGRAM_HOST, TELEGRAM_PORT))
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            class_logger.error("Port check to Telegram failed. Err msg: {}".format(str(output)))
            return False

        return True
