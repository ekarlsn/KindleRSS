#!/usr/bin/env python3
"""
发送最新生成的EPUB文件到Kindle邮箱
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

import yaml

from i18n_utils import _


def load_email_config():
    """加载邮件配置（优先使用环境变量）"""

    # 首先尝试从环境变量加载
    env_config = {
        "smtp_server": os.environ.get("SMTP_SERVER"),
        "smtp_port": os.environ.get("SMTP_PORT"),
        "sender_email": os.environ.get("SENDER_EMAIL"),
        "sender_password": os.environ.get("SENDER_PASSWORD"),
        "kindle_email": os.environ.get("KINDLE_EMAIL"),
        "subject": os.environ.get("EMAIL_SUBJECT", "RSS Feed"),
        "body": os.environ.get(
            "EMAIL_BODY", f"RSS订阅推送 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
    }

    # 检查是否所有必要的环境变量都存在
    required_fields = [
        "smtp_server",
        "smtp_port",
        "sender_email",
        "sender_password",
        "kindle_email",
    ]
    if all(env_config.get(field) for field in required_fields):
        print(_("✅ 使用环境变量配置"))
        # 转换端口为整数
        env_config["smtp_port"] = int(env_config["smtp_port"])
        return env_config

    # 如果环境变量不完整，尝试从配置文件加载
    config_file = "email_config.yaml"
    if not os.path.exists(config_file):
        print(_("❌ 配置文件 %s 不存在，且环境变量未设置") % config_file)
        print(_("请创建配置文件或设置环境变量"))
        return None

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 验证必要的配置项
    for field in required_fields:
        if field not in config:
            print(_("❌ 配置文件缺少必要字段: %s") % field)
            return None

    print(_("✅ 使用配置文件"))
    return config


def get_latest_epub():
    """获取最新生成的EPUB文件"""
    # 查找所有的EPUB文件（支持多种命名格式）
    epub_files = glob.glob("*.epub")
    if not epub_files:
        print(_("❌ 没有找到EPUB文件"))
        return None

    # 按修改时间排序，获取最新的文件
    latest_file = max(epub_files, key=os.path.getmtime)
    file_size = os.path.getsize(latest_file) / (1024 * 1024)  # 转换为MB

    print(_("📚 找到最新EPUB文件: %s") % latest_file)
    print(_("   文件大小: %.2f MB") % file_size)

    # Kindle邮件附件限制为25MB
    if file_size > 25:
        print(_("⚠️ 警告: 文件大小超过25MB，可能无法发送到Kindle"))

    return latest_file


def send_to_kindle(epub_file, config):
    """发送EPUB文件到Kindle邮箱"""
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg["From"] = config["sender_email"]
        msg["To"] = config["kindle_email"]
        msg["Subject"] = config.get("subject", "RSS Feed")

        # 添加邮件正文
        body = config.get(
            "body", f"RSS订阅推送 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # 添加EPUB附件
        with open(epub_file, "rb") as f:
            # 使用正确的MIME类型
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)

            # 确保文件名正确编码
            filename = os.path.basename(epub_file)
            # 添加Content-Type头，明确指定文件类型
            attachment.add_header("Content-Type", "application/epub+zip", name=filename)
            # 使用filename参数而不是简单的字符串格式化
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            msg.attach(attachment)

        # 连接SMTP服务器并发送
        print(_("📧 正在发送邮件到 %s...") % config["kindle_email"])

        # 根据端口选择加密方式
        if config["smtp_port"] == 587:
            # STARTTLS
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
        elif config["smtp_port"] == 465:
            # SSL
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        else:
            # 无加密
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])

        server.login(config["sender_email"], config["sender_password"])
        server.send_message(msg)
        server.quit()

        print(_("✅ 邮件发送成功！"))
        print(_("   请检查Kindle设备或邮箱确认接收"))

        return True

    except Exception as e:
        print(_("❌ 发送邮件失败: %s") % e)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description=_("发送EPUB文件到Kindle邮箱"))
    parser.add_argument("-f", "--file", help=_("指定要发送的EPUB文件"))
    parser.add_argument(
        "-c", "--config", default="email_config.yaml", help=_("指定配置文件")
    )
    args = parser.parse_args()

    # 加载配置
    config = load_email_config()
    if not config:
        print("\n" + _("请创建 email_config.yaml 文件，参考 email_config_example.yaml"))
        return

    # 获取EPUB文件
    if args.file:
        if not os.path.exists(args.file):
            print(_("❌ 指定的文件不存在: %s") % args.file)
            return
        epub_file = args.file
        print(_("📚 使用指定文件: %s") % epub_file)
    else:
        epub_file = get_latest_epub()
        if not epub_file:
            return

    # 发送邮件
    send_to_kindle(epub_file, config)


if __name__ == "__main__":
    main()
