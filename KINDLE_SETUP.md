# Kindle Email Push Setup Guide

## Overview
Automatically send generated RSS EPUB files to your Kindle device.

## Quick Start

### 1. Configure Email Settings
Set the following environment variables with your SMTP and Kindle email details:

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
export KINDLE_EMAIL="your-kindle@kindle.com"
```

### 2. Configure Kindle Email
1. Log in to your Amazon account
2. Go to "Manage Your Content and Devices"
3. Select "Preferences" → "Personal Document Settings"
4. Note your Kindle email address (e.g., `yourname_123@kindle.com`)
5. **Important**: Add your sender email to the "Approved Personal Document E-mail List"

### 3. Usage

#### Send the Latest EPUB Manually
```bash
python send_to_kindle.py
```

#### Generate and Send Automatically
```bash
python rss_and_send.py
```

#### Generate Only, No Sending
```bash
python rss_and_send.py --no-send
```

#### Send Specific File
```bash
python send_to_kindle.py -f specific_file.epub
```

## Email Configuration Guide

All email settings are configured via environment variables. The required variables are:

| Variable | Description |
|---|---|
| `SMTP_SERVER` | SMTP server address |
| `SMTP_PORT` | SMTP port (587/465/25) |
| `SENDER_EMAIL` | Sender email address |
| `SENDER_PASSWORD` | Email password or app-specific password |
| `KINDLE_EMAIL` | Kindle receiving email address |
| `EMAIL_SUBJECT` | *(Optional)* Email subject (default: "RSS Feed") |
| `EMAIL_BODY` | *(Optional)* Email body text |

### Gmail
1. **Enable 2-Factor Authentication**
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password as `SENDER_PASSWORD`

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"  # Not your regular password!
export KINDLE_EMAIL="your-kindle@kindle.com"
```

### Outlook/Hotmail
```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@outlook.com"
export SENDER_PASSWORD="your-password"
export KINDLE_EMAIL="your-kindle@kindle.com"
```

### QQ Mail
1. **Enable SMTP service** in QQ Mail settings
2. **Get authorization code** (not your QQ password)

```bash
export SMTP_SERVER="smtp.qq.com"
export SMTP_PORT="587"  # or 465 for SSL
export SENDER_EMAIL="your-email@qq.com"
export SENDER_PASSWORD="your-authorization-code"  # Not QQ password!
export KINDLE_EMAIL="your-kindle@kindle.com"
```

### 163 Mail
1. **Enable SMTP/POP3 service** in 163 Mail settings
2. **Get authorization code**

```bash
export SMTP_SERVER="smtp.163.com"
export SMTP_PORT="465"  # SSL
export SENDER_EMAIL="your-email@163.com"
export SENDER_PASSWORD="your-authorization-code"
export KINDLE_EMAIL="your-kindle@kindle.com"
```

### Other SMTP Servers
For other email providers, you need:
- SMTP server address
- SMTP port (usually 587 for STARTTLS, 465 for SSL)
- Email address and password/authorization code

## Kindle Setup Details

### Finding Your Kindle Email
1. Visit [Amazon Manage Your Content and Devices](https://www.amazon.com/mn/dcw/myx.html)
2. Go to "Preferences" tab
3. Find "Personal Document Settings"
4. Your Kindle email is listed under "Send-to-Kindle E-Mail Settings"

### Adding Approved Sender
**Critical Step**: You must add your sender email to the whitelist:

1. In "Personal Document Settings"
2. Find "Approved Personal Document E-mail List"
3. Click "Add a new approved e-mail address"
4. Enter your sender email address exactly
5. Click "Add Address"

### Kindle Email Formats
- **Kindle devices**: `username@kindle.com`
- **Kindle apps**: `username@kindle.com`
- **Multiple devices**: Each device may have a different email



## Troubleshooting

### Common Issues

#### 1. Kindle Not Receiving Emails
**Possible Causes:**
- Sender email not in approved list
- Incorrect Kindle email address
- File size exceeds 25MB limit
- Email went to spam folder

**Solutions:**
- Double-check approved sender list
- Verify Kindle email address
- Check file size with `ls -lh *.epub`
- Check Amazon account email spam folder

#### 2. Authentication Errors
**Gmail:**
- Use app password, not regular password
- Enable 2-factor authentication first

**QQ/163 Mail:**
- Use authorization code, not login password
- Enable SMTP service in email settings

**Other providers:**
- Check if "less secure apps" needs to be enabled
- Verify SMTP settings are correct

#### 3. Connection Errors
**Error:** "Connection refused" or timeout
- Check SMTP server and port
- Verify network connectivity
- Try different ports (587, 465, 25)

**Error:** "SSL/TLS errors"
- For port 587: STARTTLS
- For port 465: SSL/TLS
- For port 25: Usually no encryption

#### 4. File Size Issues
**Error:** "File too large"
- Kindle email limit: 25MB per attachment
- Compress images by setting lower quality
- Reduce `max_history` in RSS config
- Split into multiple smaller files

### Testing Email Configuration

Test your email setup:

```bash
# Test with a small file first
echo "Test content" > test.txt
python send_to_kindle.py -f test.txt

# Check the output for error messages
# Look for "✅ Email sent successfully!"
```

### Log Analysis

Common log messages and meanings:

- `❌ Missing required environment variables` - Set the variables listed in the error message
- `❌ Authentication failed` - Wrong password/authorization code
- `❌ Connection refused` - Wrong server/port or network issue
- `⚠️ File size exceeds 25MB` - File too large for Kindle email

## Advanced Configuration

### Custom Email Subject and Body

Customize the email subject and body via environment variables:

```bash
export EMAIL_SUBJECT="Daily RSS Digest"
export EMAIL_BODY="Your daily RSS digest is ready!"
```

### Multiple Kindle Devices

To send to multiple Kindle addresses, run the script multiple times with a different `KINDLE_EMAIL`:

```bash
# Send to first Kindle
KINDLE_EMAIL="kindle1@kindle.com" python send_to_kindle.py

# Send to second Kindle
KINDLE_EMAIL="kindle2@kindle.com" python send_to_kindle.py
```

### Scheduling with Cron

Set up automatic daily sending:

```bash
# Edit crontab
crontab -e

# Add line to run daily at 7 AM
0 7 * * * cd /path/to/KindleRSS && python3 rss_and_send.py

# Or with logging
0 7 * * * cd /path/to/KindleRSS && python3 rss_and_send.py >> kindle_rss.log 2>&1
```

## Security Best Practices

1. **Use App Passwords**: Never use your main email password
2. **Protect Environment Variables**: Avoid logging or exposing env vars in shell history; use a `.env` file with restricted permissions if needed
3. **Regular Rotation**: Periodically rotate app passwords
4. **Monitor Access**: Check your email account for unusual activity

## Support

For additional help:

1. **Check Email Provider Documentation**:
   - Gmail: [App Passwords Help](https://support.google.com/accounts/answer/185833)
   - Outlook: [SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)

2. **Amazon Kindle Support**:
   - [Send Documents to Kindle](https://www.amazon.com/gp/help/customer/display.html?nodeId=GX9XLEVV8G4DB28H)

3. **Project Issues**: [GitHub Issues](https://github.com/ZRui-C/KindleRSS/issues)

## FAQ

**Q: Can I send to Kindle apps on phone/tablet?**
A: Yes, use the same Kindle email address.

**Q: How often can I send emails to Kindle?**
A: Amazon doesn't specify limits, but avoid excessive sending.

**Q: Can I send other file types besides EPUB?**
A: Kindle supports PDF, MOBI, AZW, TXT, but EPUB is recommended.

**Q: Why do I need an app password for Gmail?**
A: Google requires app-specific passwords for third-party applications when 2FA is enabled.

**Q: The email was sent but Kindle didn't receive it?**
A: Check your Amazon account email (not Kindle email) for delivery confirmation or error messages.