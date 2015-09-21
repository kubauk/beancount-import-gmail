import mailbox
import os
import tempfile
from paypal_email.parser import extract_transaction

__author__ = 'picasso'


def extract_mbox(tar, mbox_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        tar.extract(mbox_file, temp_dir)
        extracted_mbox = os.path.join(temp_dir, mbox_file.name)
        process_mbox(extracted_mbox)


def process_mbox(mbox_path):
    mail_box = mailbox.mbox(mbox_path)
    for key, message in mail_box.items():
        if key == 145:
            continue

    extract_transaction(message)