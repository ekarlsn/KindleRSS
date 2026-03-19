#!/usr/bin/env python3
"""
Send the latest generated EPUB file to a Kindle email address.
"""

import argparse
import glob
import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_email_config():
    """Load email configuration from environment variables"""

    env_config = {
        "smtp_server": os.environ.get("SMTP_SERVER"),
        "smtp_port": os.environ.get("SMTP_PORT"),
        "sender_email": os.environ.get("SENDER_EMAIL"),
        "sender_password": os.environ.get("SENDER_PASSWORD"),
        "kindle_email": os.environ.get("KINDLE_EMAIL"),
        "subject": os.environ.get("EMAIL_SUBJECT", "RSS Feed"),
        "body": os.environ.get(
            "EMAIL_BODY",
            f"RSS Feed - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ),
    }

    # Check if all required environment variables are present
    required_fields = [
        "smtp_server",
        "smtp_port",
        "sender_email",
        "sender_password",
        "kindle_email",
    ]
    missing = [f for f in required_fields if not env_config.get(f)]
    if missing:
        print(
            "❌ Missing required environment variables: %s" % ", ".join(missing).upper()
        )
        return None

    print("✅ Using environment variable configuration")
    env_config["smtp_port"] = int(env_config["smtp_port"])
    return env_config


def get_latest_epub():
    """Get the most recently generated EPUB file"""
    # Find all EPUB files (supports various naming formats)
    epub_files = glob.glob("*.epub")
    if not epub_files:
        print("❌ No EPUB file found")
        return None

    # Sort by modification time and get the latest file
    latest_file = max(epub_files, key=os.path.getmtime)
    file_size = os.path.getsize(latest_file) / (1024 * 1024)  # Convert to MB

    print("📚 Latest EPUB file found: %s" % latest_file)
    print("   File size: %.2f MB" % file_size)

    # Kindle email attachment limit is 25MB
    if file_size > 25:
        print("⚠️ Warning: File size exceeds 25MB, may not be deliverable to Kindle")

    return latest_file


def send_to_kindle(epub_file, config):
    """Send an EPUB file to a Kindle email address"""
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = config["sender_email"]
        msg["To"] = config["kindle_email"]
        msg["Subject"] = config.get("subject", "RSS Feed")

        # Add email body
        body = config.get(
            "body", f"RSS Feed - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Add EPUB attachment
        with open(epub_file, "rb") as f:
            # Use the correct MIME type
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)

            # Ensure the filename is correctly encoded
            filename = os.path.basename(epub_file)
            # Add Content-Type header with explicit file type
            attachment.add_header("Content-Type", "application/epub+zip", name=filename)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            msg.attach(attachment)

        # Connect to the SMTP server and send
        print("📧 Sending email to %s..." % config["kindle_email"])

        # Choose encryption method based on port
        if config["smtp_port"] == 587:
            # STARTTLS
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
        elif config["smtp_port"] == 465:
            # SSL
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        else:
            # No encryption
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])

        server.login(config["sender_email"], config["sender_password"])
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully!")
        print("   Please check your Kindle device or email to confirm receipt")

        return True

    except Exception as e:
        print("❌ Email sending failed: %s" % e)
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Send EPUB file to Kindle email")
    parser.add_argument("-f", "--file", help="Specify the EPUB file to send")
    args = parser.parse_args()

    # Load configuration
    config = load_email_config()
    if not config:
        print(
            "\nPlease set the required environment variables: SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, KINDLE_EMAIL"
        )
        return

    # Get EPUB file
    if args.file:
        if not os.path.exists(args.file):
            print("❌ Specified file does not exist: %s" % args.file)
            return
        epub_file = args.file
        print("📚 Using specified file: %s" % epub_file)
    else:
        epub_file = get_latest_epub()
        if not epub_file:
            return

    # Send email
    send_to_kindle(epub_file, config)


if __name__ == "__main__":
    main()
