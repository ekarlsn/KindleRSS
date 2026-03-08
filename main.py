import argparse
import base64
import io
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import feedparser
import requests
import urllib3
import yaml
from bs4 import BeautifulSoup
from ebooklib import epub
from PIL import Image
from readability import Document

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config(file_path: str):
    """Load configuration (environment variables take priority over file)"""

    # Try loading full config from environment variables first (supports GitHub Variables)
    env_config = os.environ.get("CONFIG_YAML") or os.environ.get("RSS_CONFIG")
    if env_config:
        try:
            # Try parsing as YAML
            config = yaml.safe_load(env_config)
            print("✅ Using environment variable configuration (YAML format)")
            return config
        except yaml.YAMLError:
            try:
                # Try parsing as JSON
                config = json.loads(env_config)
                print("✅ Using environment variable configuration (JSON format)")
                return config
            except json.JSONDecodeError:
                print(
                    "⚠️ Environment variable configuration format error, trying file configuration"
                )

    # Load from file
    config_file = os.environ.get("CONFIG_FILE", file_path)
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print("✅ Using configuration file: %s" % config_file)
        return config

    raise FileNotFoundError("Configuration file or environment variables not found")


def fetch_feed(url):
    """Fetch an RSS feed"""
    return feedparser.parse(url)


def filter_entries(entries, max_history):
    """Filter RSS entries by date"""
    if max_history <= 0:
        return entries
    cutoff_date = datetime.now() - timedelta(days=max_history)
    filtered = []
    for entry in entries:
        if "published_parsed" in entry:
            entry_date = datetime(*entry.published_parsed[:6])
            if entry_date >= cutoff_date:
                filtered.append(entry)
    return filtered


def sanitize_filename(name):
    """Remove illegal characters from a filename"""
    return "".join(c if c.isalnum() else "_" for c in name)


def resolve_link_content(url, config=None):
    """Parse content from the original article link.

    Args:
        url: URL to parse
        config: Parsing configuration, including selectors etc.

    Returns:
        Parsed HTML content, or None on failure
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = requests.get(url, headers=headers, timeout=15, verify=False)
        if response.status_code != 200:
            return None

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # If the config has selectors, use them first
        if config and isinstance(config, dict):
            # Option 1: CSS selector extraction
            if "selectors" in config:
                selectors = config["selectors"]

                # Remove unwanted elements
                if "remove" in selectors:
                    remove_selectors = selectors["remove"]
                    if isinstance(remove_selectors, str):
                        remove_selectors = [
                            s.strip() for s in remove_selectors.split(",")
                        ]

                    for selector in remove_selectors:
                        for elem in soup.select(selector):
                            elem.decompose()

                # Extract content
                if "content" in selectors:
                    content_selectors = selectors["content"]
                    if isinstance(content_selectors, str):
                        content_selectors = [
                            s.strip() for s in content_selectors.split(",")
                        ]

                    extracted_content = []
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            for elem in elements:
                                extracted_content.append(str(elem))
                            break  # Stop at first matching selector

                    if extracted_content:
                        return "\n".join(extracted_content)

            # If config specifies readability or selector fails, use fallback
            if (
                config.get("method") == "readability"
                or config.get("fallback") == "readability"
            ):
                # Option 2: Use readability for automatic extraction
                doc = Document(html_content)
                return doc.summary()

        # Default: use readability
        doc = Document(html_content)
        return doc.summary()

    except Exception as e:
        print("Link parsing failed %s: %s" % (url, e))
        return None


def extract_images_from_html(html_content):
    """Extract image URLs from HTML content"""
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    return re.findall(img_pattern, html_content, re.IGNORECASE)


def download_image_as_base64(url, timeout=10):
    """Download an image and convert it to base64; WebP is automatically converted to JPEG"""
    try:
        # Full request headers to simulate a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
        }

        # Add Referer header (inferred from URL)
        parsed = urlparse(url)
        if parsed.netloc:
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

        response = requests.get(url, timeout=timeout, headers=headers, verify=False)
        if response.status_code == 200:
            # Get image content type
            content_type = response.headers.get("content-type", "image/jpeg")
            if "image" in content_type or len(response.content) > 100:
                # Check if WebP format
                is_webp = "webp" in content_type.lower() or url.lower().endswith(
                    ".webp"
                )

                if is_webp:
                    try:
                        # Convert WebP to JPEG
                        img = Image.open(io.BytesIO(response.content))
                        # Convert RGBA to RGB if needed
                        if img.mode == "RGBA":
                            # Create white background
                            background = Image.new("RGB", img.size, (255, 255, 255))
                            background.paste(
                                img, mask=img.split()[3]
                            )  # Use alpha channel as mask
                            img = background
                        elif img.mode != "RGB":
                            img = img.convert("RGB")

                        # Convert to JPEG
                        output = io.BytesIO()
                        img.save(output, format="JPEG", quality=85)
                        img_data = output.getvalue()
                        img_base64 = base64.b64encode(img_data).decode("utf-8")
                        content_type = "image/jpeg"
                    except Exception:
                        # If conversion fails, use original data
                        img_base64 = base64.b64encode(response.content).decode("utf-8")
                else:
                    # Non-WebP, use directly
                    img_base64 = base64.b64encode(response.content).decode("utf-8")

                # If no clear content-type, infer from URL
                if "image" not in content_type:
                    if ".png" in url.lower():
                        content_type = "image/png"
                    elif ".gif" in url.lower():
                        content_type = "image/gif"
                    else:
                        content_type = "image/jpeg"
                return f"data:{content_type};base64,{img_base64}"
    except Exception:
        # Silently handle errors to avoid excessive output
        pass
    return None


def process_content_images(content, load_images=True):
    """Process images in content, converting them to embedded base64"""
    if not load_images:
        # Remove all img tags if images are disabled
        return re.sub(r"<img[^>]*>", "", content)

    # Extract all image URLs
    img_urls = extract_images_from_html(content)

    # Track successfully downloaded images
    embedded_images = []

    # Replace image URLs with base64
    for img_url in img_urls:
        base64_img = download_image_as_base64(img_url)
        if base64_img:
            # Create new img tag with correct format
            new_img_tag = f'<img src="{base64_img}" alt="Image"/>'
            # Replace the original img tag
            img_pattern = f"<img[^>]*src=[\"']?{re.escape(img_url)}[\"']?[^>]*>"
            content = re.sub(img_pattern, new_img_tag, content)
            embedded_images.append(img_url[:50])

    if embedded_images:
        print("  ✓ Successfully embedded %d images" % len(embedded_images))

    return content


def download_and_add_image(book, url, img_id):
    """Download an image and add it to the EPUB book; WebP is automatically converted to JPEG"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": urlparse(url).scheme + "://" + urlparse(url).netloc + "/",
        }

        response = requests.get(url, timeout=10, headers=headers, verify=False)
        if response.status_code == 200 and len(response.content) > 100:
            # Determine image type
            content_type = response.headers.get("content-type", "")
            img_content = response.content

            # Check if WebP format
            is_webp = "webp" in content_type.lower() or url.lower().endswith(".webp")

            if is_webp:
                try:
                    # Convert WebP to JPEG
                    img = Image.open(io.BytesIO(response.content))
                    # Convert RGBA to RGB if needed
                    if img.mode == "RGBA":
                        # Create white background
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(
                            img, mask=img.split()[3]
                        )  # Use alpha channel as mask
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                    # Convert to JPEG
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=85)
                    img_content = output.getvalue()
                    ext = "jpg"
                    media_type = "image/jpeg"
                except Exception:
                    # If conversion fails, keep original WebP
                    ext = "webp"
                    media_type = "image/webp"
            elif "png" in content_type or ".png" in url.lower():
                ext = "png"
                media_type = "image/png"
            elif "gif" in content_type or ".gif" in url.lower():
                ext = "gif"
                media_type = "image/gif"
            else:
                ext = "jpg"
                media_type = "image/jpeg"

            # Create EPUB image item
            img_name = f"img_{img_id}.{ext}"
            img_item = epub.EpubImage()
            img_item.uid = f"image_{img_id}"
            img_item.file_name = f"images/{img_name}"
            img_item.media_type = media_type
            img_item.content = img_content

            book.add_item(img_item)
            return f"images/{img_name}"
    except Exception:
        pass
    return None


def convert_to_epub(feeds, load_images=True, feeds_config=None, custom_filename=None):
    """Convert RSS feeds into a formatted EPUB e-book"""
    book = epub.EpubBook()

    # Set book metadata
    current_date = datetime.now()
    book.set_identifier(f"rss-compilation-{current_date.strftime('%Y%m%d%H%M%S')}")
    book.set_title("RSS Feed")
    book.set_language("en")
    book.add_author("KindleRSS")
    book.add_metadata("DC", "description", "Curated RSS subscription content")
    book.add_metadata("DC", "date", current_date.strftime("%Y-%m-%d"))

    # Create custom main table of contents page
    main_toc_page = epub.EpubHtml(
        title="Table of Contents", file_name="main_toc.xhtml", lang="en"
    )
    main_toc_content = f"""
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Table of Contents</title>
        <style>
            a {{ color: black; text-decoration: underline; }}
            ul {{ margin: 30px auto; max-width: 600px; }}
            li {{ margin: 15px 0; }}
            img {{
                page-break-inside: avoid;
                break-inside: avoid;
                display: block;
                max-width: 100%;
                height: auto;
            }}
            figure {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
        </style>
    </head>
    <body>
        <center>
            <h1>RSS Feed</h1>
            <p>{datetime.now().strftime("%Y-%m-%d")}</p>
        </center>
        <br/>
        <ul>
    """

    book.spine = ["nav", main_toc_page]  # nav first, then custom TOC
    book.toc = []
    all_articles = []  # Store all articles for navigation
    img_counter = 0  # Image counter
    feed_index_pages = []  # Store all feed index page info

    feed_list = list(feeds.items())
    for feed_idx, (feed_key, feed_data) in enumerate(feed_list):
        # Handle both new and old data format
        if isinstance(feed_data, dict) and "entries" in feed_data:
            entries = feed_data["entries"]
            feed_meta = feed_data.get("feed_meta", {})
        else:
            # Compatible with old format (entries list directly)
            entries = feed_data
            feed_meta = {}

        # Use feed title from metadata, falling back to feed_key
        feed_name = feed_meta.get("title", feed_key)

        if not entries:
            continue

        # Create feed index page (secondary TOC)
        index_file = sanitize_filename(feed_name) + "_toc.xhtml"
        feed_index_page = epub.EpubHtml(
            title=feed_name, file_name=index_file, lang="en"
        )

        # Add to main TOC page
        main_toc_content += (
            f'            <li><a href="{index_file}">{feed_name}</a></li>\n'
        )

        # Determine previous/next navigation
        prev_feed_link = ""
        next_feed_link = ""
        if feed_idx > 0:
            # Get the previous feed's name
            prev_key, prev_data = feed_list[feed_idx - 1]
            if isinstance(prev_data, dict) and "entries" in prev_data:
                prev_name = prev_data.get("config_name") or prev_data.get(
                    "feed_meta", {}
                ).get("title", prev_key)
            else:
                prev_name = prev_key
            prev_feed_file = sanitize_filename(prev_name) + "_toc.xhtml"
            prev_feed_link = f'<a href="{prev_feed_file}">Prev</a>'
        if feed_idx < len(feed_list) - 1:
            # Get the next feed's name
            next_key, next_data = feed_list[feed_idx + 1]
            if isinstance(next_data, dict) and "entries" in next_data:
                next_name = next_data.get("config_name") or next_data.get(
                    "feed_meta", {}
                ).get("title", next_key)
            else:
                next_name = next_key
            next_feed_file = sanitize_filename(next_name) + "_toc.xhtml"
            next_feed_link = f'<a href="{next_feed_file}">Next</a>'

        # Build navigation bar
        nav_parts = []
        has_prev = bool(prev_feed_link)
        has_next = bool(next_feed_link)

        if has_prev and has_next:
            # Full navigation: Prev | Main menu | Next
            nav_parts.append(prev_feed_link)
            nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
            nav_parts.append(next_feed_link)
        elif has_prev and not has_next:
            # Last feed: Previous | Main menu
            prev_feed_link = prev_feed_link.replace(">Prev<", ">Previous<")
            nav_parts.append(prev_feed_link)
            nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
        elif not has_prev and has_next:
            # First feed: Main menu | Next
            nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
            nav_parts.append(next_feed_link)
        else:
            # Only one feed: Main menu
            nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')

        navigation_bar = " | ".join(nav_parts)

        # Get feed subtitle
        feed_subtitle = ""
        if "title_detail" in feed_meta and "subtitle" in feed_meta.get(
            "title_detail", {}
        ):
            feed_subtitle = feed_meta["title_detail"]["subtitle"]
        elif "subtitle" in feed_meta:
            feed_subtitle = feed_meta.get("subtitle", "")

        # Build feed index page content
        index_content = f"""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>{feed_name}</title>
            <style>
                a {{ color: black; text-decoration: underline; }}
                .nav {{ margin: 20px 0; padding: 10px; }}
                .description-preview {{
                    color: #666;
                    font-size: 0.9em;
                    margin-left: 20px;
                    margin-top: 5px;
                }}
                img {{
                    page-break-inside: avoid;
                    break-inside: avoid;
                    display: block;
                    max-width: 100%;
                    height: auto;
                }}
                figure {{
                    page-break-inside: avoid;
                    break-inside: avoid;
                }}
            </style>
        </head>
        <body>
            <center>
                <div class="nav">{navigation_bar}</div>
            </center>
            <hr/>
            <center>
                <h1>{feed_name}</h1>
                {f"<p><i>{feed_subtitle}</i></p>" if feed_subtitle else ""}
            </center>
            <ul>
        """

        # Process each article
        article_toc = []
        feed_articles = []  # Articles in the current feed

        for idx, entry in enumerate(entries, 1):
            entry_file = f"{sanitize_filename(feed_name)}_{idx:03d}.xhtml"

            # Get publication date
            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).strftime(
                    "%Y-%m-%d %H:%M"
                )
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6]).strftime(
                    "%Y-%m-%d %H:%M"
                )

            # Get description preview (first 100 characters)
            description_preview = ""
            raw_desc = entry.get("summary", entry.get("description", ""))
            if raw_desc:
                # Strip HTML tags
                clean_desc = re.sub(r"<[^>]+>", "", raw_desc)
                clean_desc = clean_desc.strip()
                if len(clean_desc) > 100:
                    description_preview = clean_desc[:100] + "[...]"
                else:
                    description_preview = clean_desc

            # Add to index page (HTML list)
            index_content += f'''
                <li>
                    <a href="{entry_file}">{entry.title} - {pub_date}</a>
                    {f'<div class="description-preview">{description_preview}</div>' if description_preview else ""}
                </li>
            '''

            # Create article page
            chapter = epub.EpubHtml(title=entry.title, file_name=entry_file, lang="en")

            # Store article info for navigation
            article_info = {
                "chapter": chapter,
                "feed_name": feed_name,
                "index_file": index_file,
                "entry_file": entry_file,
                "title": entry.title,
                "feed_idx": feed_idx,
            }
            feed_articles.append(article_info)
            all_articles.append(article_info)

            # Get and process article content
            raw_content = entry.get(
                "summary", entry.get("description", "No summary available")
            )

            # Check if we need to resolve content from the original link
            feed_config = feeds_config.get(feed_name, {}) if feeds_config else {}
            resolve_config = feed_config.get("resolve_link", {"method": "readability"})

            if resolve_config and entry.get("link"):
                resolved_content = resolve_link_content(entry.link, resolve_config)
                if resolved_content:
                    # Successfully resolved, use parsed content
                    raw_content = resolved_content
                    print("  ✓ Parsed original content: %s..." % entry.title[:30])
                else:
                    print(
                        "  ✗ Unable to parse original content, using RSS summary: %s..."
                        % entry.title[:30]
                    )

            # Process images in the content
            processed_content = raw_content
            if load_images:
                # Extract and replace images
                img_urls = extract_images_from_html(raw_content)
                for img_url in img_urls:
                    img_counter += 1
                    local_img = download_and_add_image(book, img_url, img_counter)
                    if local_img:
                        # Replace with local image path
                        img_pattern = (
                            f"<img[^>]*src=[\"']?{re.escape(img_url)}[\"']?[^>]*>"
                        )
                        new_img = f'<img src="{local_img}" alt="Image"/>'
                        processed_content = re.sub(
                            img_pattern, new_img, processed_content
                        )
            else:
                # Remove all image tags
                processed_content = re.sub(r"<img[^>]*>", "", processed_content)

            # Save base content; navigation will be added later
            article_base_content = f"""
                <hr/>
                <center><h1>{entry.title}</h1></center>
                <p>
                    <small>
                        {f"Published: {pub_date}" if pub_date else ""}
                        {f"Source: {feed_name}" if feed_name else ""}
                    </small>
                </p>
                <br/>
                <blockquote>
                    {processed_content}
                </blockquote>
            """

            # Handle additional media images if present
            if load_images:
                extra_images = []

                # Collect extra media images
                if hasattr(entry, "media_content") and entry.media_content:
                    for media in entry.media_content:
                        if "url" in media:
                            extra_images.append(media["url"])
                elif hasattr(entry, "enclosures") and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if enclosure.type and enclosure.type.startswith("image/"):
                            extra_images.append(enclosure.href)

                # Download and embed extra images if any
                if extra_images:
                    article_base_content += "<br/><h2>&#9635; Additional Images</h2>"
                    for img_url in extra_images:
                        img_counter += 1
                        local_img = download_and_add_image(book, img_url, img_counter)
                        if local_img:
                            article_base_content += (
                                f'<p><img src="{local_img}" alt="Article image"/></p>'
                            )
                        else:
                            # If download fails, use original URL
                            article_base_content += (
                                f'<p><img src="{img_url}" alt="Article image"/></p>'
                            )

            # Save content temporarily; navigation will be added later
            chapter.base_content = article_base_content
            book.add_item(chapter)
            article_toc.append(chapter)

        # Add navigation to each article in the current feed
        for i, article_info in enumerate(feed_articles):
            # Build navigation elements
            nav_parts = []

            has_prev = i > 0
            has_next = i < len(feed_articles) - 1

            if has_prev and has_next:
                # Full navigation: Prev | Sec | Main menu | Next
                nav_parts.append(
                    f'<a href="{feed_articles[i - 1]["entry_file"]}">Prev</a>'
                )
                nav_parts.append(f'<a href="{index_file}">Sec</a>')
                nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
                nav_parts.append(
                    f'<a href="{feed_articles[i + 1]["entry_file"]}">Next</a>'
                )
            elif has_prev and not has_next:
                # Last article: Prev | Sec | Main menu
                nav_parts.append(
                    f'<a href="{feed_articles[i - 1]["entry_file"]}">Prev</a>'
                )
                nav_parts.append(f'<a href="{index_file}">Sec</a>')
                nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
            elif not has_prev and has_next:
                # First article: Sec | Main menu | Next
                nav_parts.append(f'<a href="{index_file}">Sec</a>')
                nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')
                nav_parts.append(
                    f'<a href="{feed_articles[i + 1]["entry_file"]}">Next</a>'
                )
            else:
                # Only one article: Section | Main menu
                nav_parts.append(f'<a href="{index_file}">Section</a>')
                nav_parts.append('<a href="main_toc.xhtml">Main menu</a>')

            navigation_bar = " | ".join(nav_parts)

            # Build the full article page
            article_content = f"""
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>{article_info["title"]}</title>
                <style>
                    a {{ color: black; text-decoration: underline; }}
                    .nav {{ margin: 20px 0; padding: 10px; }}
                    img {{
                        page-break-inside: avoid;
                        break-inside: avoid;
                        display: block;
                        max-width: 100%;
                        height: auto;
                    }}
                    figure {{
                        page-break-inside: avoid;
                        break-inside: avoid;
                    }}
                    p {{
                        orphans: 2;
                        widows: 2;
                    }}
                </style>
            </head>
            <body>
                <center>
                    <div class="nav">{navigation_bar}</div>
                </center>
                {article_info["chapter"].base_content}
            </body>
            </html>
            """

            article_info["chapter"].content = article_content
            del article_info["chapter"].base_content

        # Finish the index page and add bottom navigation
        index_content += f"""
            </ul>
            <hr/>
            <center>
                <div class="nav">{navigation_bar}</div>
            </center>
        </body>
        </html>
        """

        feed_index_page.content = index_content
        book.add_item(feed_index_page)
        book.spine.append(feed_index_page)  # Add index page first

        # Then add all articles for this feed
        for chapter in article_toc:
            book.spine.append(chapter)

        # Add to built-in TOC
        book.toc.append(feed_index_page)

    # Finish the main TOC page
    main_toc_content += """
        </ul>
    </body>
    </html>
    """
    main_toc_page.content = main_toc_content
    book.add_item(main_toc_page)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Generate filename
    if custom_filename:
        # Use custom filename, replacing date placeholders
        current_date = datetime.now()
        replacements = {
            "{year}": str(current_date.year),
            "{month}": f"{current_date.month:02d}",
            "{day}": f"{current_date.day:02d}",
            "{hour}": f"{current_date.hour:02d}",
            "{minute}": f"{current_date.minute:02d}",
            "{second}": f"{current_date.second:02d}",
            "{date}": current_date.strftime("%Y-%m-%d"),
            "{time}": current_date.strftime("%H:%M"),
            "{datetime}": current_date.strftime("%Y-%m-%d_%H-%M"),
        }
        filename = custom_filename
        for placeholder, value in replacements.items():
            filename = filename.replace(placeholder, value)

        # Ensure the file extension is .epub
        if not filename.endswith(".epub"):
            filename += ".epub"
    else:
        # Default filename format
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        filename = f"rss_feed_{timestamp}.epub"

    # Write EPUB
    epub.write_epub(filename, book, {})
    print("✅ EPUB e-book generated: %s" % filename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()


def main():
    args = parse_args()
    generate_epub(args.config)


def generate_epub(config_path: str):
    config = load_config(config_path)
    all_feeds = {}
    feeds_config = {}  # Store config for each feed

    for feed in config["Feeds"]:
        if feed.get("enabled", True):
            parsed_feed = fetch_feed(feed["url"])
            entries = filter_entries(
                parsed_feed.entries, config["Settings"].get("max_history", -1)
            )

            # Save the feed title and metadata
            feed_title = feed.get("title", feed["url"])

            all_feeds[feed_title] = {
                "entries": entries,
                "feed_meta": parsed_feed.feed,  # Contains feed metadata
            }
            feeds_config[feed_title] = feed

    # Get custom filename template if configured
    custom_filename = config.get("Settings", {}).get("filename_template")

    convert_to_epub(
        all_feeds,
        config["Settings"].get("load_images", True),
        feeds_config,
        custom_filename,
    )


if __name__ == "__main__":
    main()
