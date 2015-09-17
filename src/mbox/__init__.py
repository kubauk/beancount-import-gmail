import mailbox
import os
import tempfile
from paypal_email.parser import process_email

__author__ = 'picasso'


def extract_mbox(transactions, tar, mbox_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        tar.extract(mbox_file, temp_dir)
        extracted_mbox = os.path.join(temp_dir, mbox_file.name)
        process_mbox(transactions, extracted_mbox)


def process_mbox(transactions, mbox_path):
    mail_box = mailbox.mbox(mbox_path)
    for key, message in mail_box.items():
        if key == 145:
            continue
        process_email(transactions, message)