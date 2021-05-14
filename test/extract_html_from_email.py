import os.path
import sys
from email import message_from_file
from email.message import Message


def extract_html_from(file: str) -> None:
    with open(file) as f:
        email = message_from_file(f)

    if email.is_multipart():
        for part in email.get_payload():
            if "text/html" in part.get_content_type():
                write_html(file, part)
    else:
        write_html(file, email)


def write_html(file: str, message: Message) -> None:
    with open("{}.html".format(os.path.basename(file)), 'w') as f:
        f.write(message.get_payload(decode=True).decode(message.get_content_charset()))


if __name__ == '__main__':
    email_file = sys.argv[1]

    print("Extract html from {}".format(email_file))
    extract_html_from(email_file)
