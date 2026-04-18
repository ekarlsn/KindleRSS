#!/usr/bin/env python3
"""
Combined script: generate EPUB and automatically send to Kindle
"""

import argparse
import sys

# Import main program and sending module
from main import generate_epub
from send_to_kindle import get_latest_epub, load_email_config, send_to_kindle

SEPARATOR = "=================================================="


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RSS EPUB and send to Kindle")
    parser.add_argument(
        "--no-send", action="store_true", help="Only generate EPUB, do not send email"
    )
    parser.add_argument(
        "--send-only",
        action="store_true",
        help="Only send the latest EPUB, do not generate new one",
    )
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.send_only:
        # Generate EPUB
        print(SEPARATOR)
        print("📖 Starting EPUB generation...")
        print(SEPARATOR)
        generate_epub(args.config)
        print("✅ EPUB generation successful!")

    if not args.no_send:
        # Send to Kindle
        print("\n" + SEPARATOR)
        print("📧 Preparing to send to Kindle...")
        print(SEPARATOR)

        # Load email configuration
        config = load_email_config()
        if not config:
            print("⚠️ Skipping email sending (configuration file not found)")
            print("   Hint: Create email_config.yaml to enable email sending")
            return 0

        # Get the latest EPUB file
        epub_file = get_latest_epub()
        if not epub_file:
            print("❌ No EPUB file found to send")
            return 1

        # Send email
        if send_to_kindle(epub_file, config):
            print("\n" + SEPARATOR)
            print("🎉 Complete! EPUB generated and sent to Kindle")
            print(SEPARATOR)
            return 0
        else:
            print("⚠️ EPUB generated but email sending failed")
            return 1

    print("\n" + SEPARATOR)
    print("✅ EPUB generation complete (email not sent)")
    print(SEPARATOR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
