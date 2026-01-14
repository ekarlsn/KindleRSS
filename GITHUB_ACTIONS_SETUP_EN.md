# GitHub Actions Automated Push Setup Guide

## Overview
Use GitHub Actions to automatically generate RSS EPUB and send to Kindle, with all sensitive information managed through GitHub Secrets.

## Setup Steps

### 1. Fork or Upload Code to GitHub

Ensure your repository contains the following files:
- `main.py` - RSS to EPUB main program
- `send_to_kindle.py` - Email sending program
- `rss_and_send.py` - Combined script
- `config.yaml` - RSS source configuration
- `.github/workflows/rss_to_kindle.yml` - GitHub Actions workflow
- `requirements.txt` - Python dependencies

### 2. Configure GitHub Secrets and Variables

#### Method 1: Using Repository Variables (Recommended)

Set Variables in your GitHub repository:

1. Go to your repository page
2. Click `Settings` → `Secrets and variables` → `Actions`
3. Select the `Variables` tab
4. Click `New repository variable`
5. Add `CONFIG_YAML` variable with complete config.yaml content

**CONFIG_YAML Example Content:**
```yaml
Settings:
  max_history: 7
  load_images: true

Feeds:
  - url: "https://sspai.com/feed"
    name: "SSPAI"
    title: "SSPAI Selected"
    enabled: true
    resolve_link:
      enabled: true
      method: "readability"
```

#### Method 2: Using Secrets (for private RSS sources)

If your RSS sources contain private information, use Secrets:

1. Select the `Secrets` tab
2. Click `New repository secret`
3. Add `RSS_CONFIG` secret with complete config.yaml content

### 3. Configure Email Secrets

Add the following Secrets (required):

- `SMTP_SERVER` - SMTP server address
- `SMTP_PORT` - SMTP port (587/465/25)
- `SENDER_EMAIL` - Sender email address
- `SENDER_PASSWORD` - Email password or app-specific password
- `KINDLE_EMAIL` - Kindle receiving email address

Optional Secrets:
- `EMAIL_SUBJECT` - Custom email subject (default: "RSS Feed")
- `EMAIL_BODY` - Custom email body

**Common SMTP Settings:**

| Email Provider | SMTP Server | Port | Security |
|---|---|---|---|
| Gmail | smtp.gmail.com | 587 | STARTTLS |
| Outlook | smtp-mail.outlook.com | 587 | STARTTLS |
| QQ Mail | smtp.qq.com | 587 | STARTTLS |
| 163 Mail | smtp.163.com | 465 | SSL |

### 4. Configure Kindle Whitelist

**Important**: Add your sender email to Kindle's approved sender list:

1. Visit [Amazon Manage Your Content and Devices](https://www.amazon.com/mn/dcw/myx.html)
2. Go to `Preferences` → `Personal Document Settings`
3. Find "Approved Personal Document E-mail List"
4. Click "Add a new approved e-mail address"
5. Enter your sender email address

### 5. Workflow Configuration

The repository includes three workflow files:

#### Basic Workflow (`rss_to_kindle.yml`)
- Runs daily at 7 AM Beijing time
- Generates EPUB and sends to Kindle
- Suitable for most users

#### Advanced Workflow (`rss_to_kindle_advanced.yml`)
- Supports manual triggers with custom parameters
- Can create GitHub Releases
- Configurable schedule

#### Test Workflow (`test.yml`)
- Runs on code pushes
- Tests EPUB generation only
- No email sending

### 6. Manual Trigger

To manually run the workflow:

1. Go to your repository
2. Click `Actions` tab
3. Select `RSS to Kindle` workflow
4. Click `Run workflow`
5. Fill in parameters (if using advanced workflow)
6. Click `Run workflow`

## Configuration Examples

### Complete Variable Configuration

```yaml
# CONFIG_YAML Variable Content
Settings:
  max_history: 7
  load_images: true
  filename_template: "RSS_Digest_{date}.epub"

Feeds:
  - url: "https://feeds.feedburner.com/oreilly/radar"
    name: "O'Reilly Radar"
    title: "O'Reilly Radar"
    enabled: true
    resolve_link:
      enabled: true
      method: "readability"
      fallback: "readability"

  - url: "https://www.ruanyifeng.com/blog/atom.xml"
    name: "Ruan Yifeng's Blog"
    title: "Ruan Yifeng's Network Log"
    enabled: true
    resolve_link:
      enabled: true
      method: "selector"
      selectors:
        content: "article .asset-content"
        remove: ".asset-meta, .asset-footer"
      fallback: "readability"
```

### Email Configuration (Secrets)

For Gmail (requires app-specific password):
- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SENDER_EMAIL`: `your-email@gmail.com`
- `SENDER_PASSWORD`: `your-app-password`
- `KINDLE_EMAIL`: `your-kindle@kindle.com`

## Troubleshooting

### Common Issues

1. **Workflow fails with "Config not found"**
   - Check if `CONFIG_YAML` or `RSS_CONFIG` variable is set
   - Verify YAML syntax is correct

2. **Email sending fails**
   - Verify all email Secrets are set correctly
   - Check if sender email is whitelisted in Kindle
   - For Gmail, ensure you're using app-specific password

3. **Kindle not receiving files**
   - Confirm sender email is in Kindle's approved list
   - Check if EPUB file size is under 25MB
   - Verify Kindle email address is correct

4. **Workflow doesn't run on schedule**
   - GitHub Actions may have delays
   - Try manually triggering the workflow
   - Check if repository has recent activity

### Debugging Steps

1. **Check Workflow Logs**
   - Go to Actions tab
   - Click on failed workflow run
   - Review job logs for error messages

2. **Test Configuration**
   - Use the test workflow to verify EPUB generation
   - Manually trigger workflow to test email sending

3. **Verify Secrets**
   - Ensure all required Secrets are set
   - Check for typos in Secret names
   - Verify Secret values are correct

## Advanced Features

### Custom Scheduling

Edit the workflow file to change schedule:

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # Run at 11 PM UTC daily
  workflow_dispatch:
```

### Multiple Kindle Devices

To send to multiple Kindle devices, modify the workflow to run multiple times with different email addresses, or set up separate workflows.

### Release Creation

The advanced workflow can create GitHub Releases with the generated EPUB:

```yaml
- name: Create Release
  uses: softprops/action-gh-release@v1
  with:
    files: "*.epub"
    tag_name: "rss-${{ steps.date.outputs.date }}"
```

## Security Notes

- Never commit sensitive information to the repository
- Use Secrets for all passwords and private information
- Variables are visible to repository collaborators; use Secrets for sensitive data
- Regularly rotate passwords and app-specific passwords

## Support

If you encounter issues:

1. Check the [Issues](https://github.com/ZRui-C/KindleRSS/issues) page
2. Review workflow logs for specific error messages
3. Ensure all configuration steps are completed
4. Test locally first to isolate GitHub Actions issues

For questions about specific email providers or Kindle setup, refer to:
- [Kindle Setup Guide](KINDLE_SETUP_EN.md)
- Email provider's SMTP documentation
- GitHub Actions documentation