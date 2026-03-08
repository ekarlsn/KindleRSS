# KindleRSS

Convert RSS feeds to EPUB e-books and automatically send them to your Kindle device. Supports full-text extraction, image embedding, and GitHub Actions automation.

## ✨ Features

- 📚 **RSS to EPUB** - Merge multiple RSS feeds into a beautifully formatted EPUB e-book
- 🔍 **Full-Text Extraction** - Extract complete article content from web pages (CSS selectors/Readability)
- 🖼️ **Image Processing** - Automatically download and embed article images with anti-page-break display
- 📧 **Kindle Push** - Auto-send to Kindle email
- 🤖 **GitHub Actions** - Fully automated scheduled generation and delivery
- 📖 **Smart Navigation** - Multi-level table of contents for easy reading navigation
- 🔄 **OPML Converter** - Online tool to convert OPML files to project configuration format

## 🚀 Quick Start

### Local Usage

1. **Clone Repository**
```bash
git clone https://github.com/ZRui-C/KindleRSS.git
cd KindleRSS
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure RSS Sources**
```bash
cp config.example.yaml config.yaml
# Edit config.yaml to add your RSS sources
```

4. **Generate EPUB**
```bash
python main.py
```

5. **Send to Kindle** (Optional)
```bash
# Configure email settings
cp email_config.example.yaml email_config.yaml
# Edit email_config.yaml

# Send the latest EPUB
python send_to_kindle.py

# Or generate and send
python rss_and_send.py
```

### GitHub Actions Automation

1. **Fork this repository**

2. **Configure GitHub Variables/Secrets**

   In repository settings, configure:

   **RSS Configuration** (Variables or Secrets):
   - `CONFIG_YAML` - Complete config.yaml content

   **Email Configuration** (Secrets):
   - `SMTP_SERVER` - SMTP server address
   - `SMTP_PORT` - SMTP port
   - `SENDER_EMAIL` - Sender email
   - `SENDER_PASSWORD` - Email password/app password
   - `KINDLE_EMAIL` - Kindle receiving email

3. **Configure Kindle Whitelist**

   Add sender email to Kindle's approved sender list

4. **Automatic Execution**

   - Automatic push daily at 7 AM Beijing time
   - Or trigger manually: Actions → RSS to Kindle → Run workflow

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed setup

## 🔄 OPML Converter

Visit the [Online OPML Converter](https://kindle.hluvmiku.tech/en/converter.html) to easily convert OPML files to config.yaml format:

1. Export OPML file from your RSS reader
2. Upload to the converter page
3. Automatically generate config.yaml configuration
4. Copy or download the configuration file with one click

## 📝 Configuration

### RSS Source Configuration (config.yaml)

```yaml
Settings:
  max_history: 7  # Keep articles from the last N days
  load_images: true  # Whether to download images

Feeds:
  # Minimal entry — enabled and readability full-text extraction are the defaults.
  - url: "https://example.com/rss"
    title: "Example Blog"

  # Disable a feed without removing it.
  - url: "https://example.com/other.xml"
    title: "Paused Feed"
    enabled: false

  # Override to use CSS selectors instead of readability.
  - url: "https://example.com/selector-site/feed.xml"
    title: "Selector Site"
    resolve_link:
      method: "selector"
      selectors:
        content: "article, .content"
        remove: ".ads, .comments"
      fallback: "readability"

  # Disable link resolution — use the RSS summary as-is.
  - url: "https://example.com/summary-only/feed.xml"
    title: "Summary Only Feed"
    resolve_link: false
```

### Email Configuration (email_config.yaml)

Refer to `email_config.example.yaml` to configure your SMTP server information.

Supported email services:
- Gmail (requires app-specific password)
- QQ Mail (requires authorization code)
- 163 Mail (requires authorization code)
- Outlook
- Other SMTP servers

## 📂 Project Structure

```
.
├── main.py                 # Main program: RSS to EPUB
├── send_to_kindle.py       # Kindle email sender
├── rss_and_send.py        # Combined script
├── config.yaml            # RSS source configuration
├── email_config.yaml      # Email configuration (to be created)
├── requirements.txt       # Python dependencies
├── .github/
│   └── workflows/
│       ├── rss_to_kindle.yml      # Basic workflow
│       ├── rss_to_kindle_advanced.yml  # Advanced workflow
│       └── test.yml               # Test workflow
└── README.md              # This document
```

## 🛠️ Advanced Features

### Full-Text Extraction Modes

1. **Readability Mode** - Automatically identify article body
2. **CSS Selector Mode** - Precisely specify content areas
3. **Hybrid Mode** - Automatically switch to Readability when selector fails

### Scheduled Tasks

Set up local scheduled tasks using crontab:
```bash
# Run daily at 7 AM
0 7 * * * cd /path/to/rss-to-epub && python3 rss_and_send.py
```

### GitHub Actions Workflows

- **Basic Version** - Daily automatic push
- **Advanced Version** - Supports Release publishing, custom timing
- **Test Version** - Automatic testing on code commits

## 🔧 Troubleshooting

### Common Issues

1. **Kindle not receiving emails**
   - Check if sender email is whitelisted
   - Confirm file size is under 25MB
   - Check spam folder

2. **Email sending failure**
   - Verify SMTP settings
   - Confirm using app-specific password/authorization code
   - Check network connection

3. **RSS parsing failure**
   - Confirm RSS source URL is correct
   - Check network accessibility
   - See if proxy is needed

## 📖 Documentation

- [Kindle Push Setup](KINDLE_SETUP.md)
- [GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md)
- [Configuration Example](config.example.yaml)

## 📄 License

MIT License

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 🙏 Acknowledgments

- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB generation library
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS parsing library
- [readability-lxml](https://github.com/buriy/python-readability) - Web content extraction

---

For questions or suggestions, please submit an [Issue](https://github.com/ZRui-C/KindleRSS/issues).