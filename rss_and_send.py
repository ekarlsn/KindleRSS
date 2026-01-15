#!/usr/bin/env python3
"""
组合脚本：生成EPUB并自动发送到Kindle
"""

import argparse
import os
import sys
from datetime import datetime

from i18n_utils import _

# 导入主程序和发送模块
from main import main as generate_epub
from send_to_kindle import get_latest_epub, load_email_config, send_to_kindle


def main():
    """主函数：生成并发送"""
    parser = argparse.ArgumentParser(description=_("生成RSS EPUB并发送到Kindle"))
    parser.add_argument(
        "--no-send", action="store_true", help=_("仅生成EPUB，不发送邮件")
    )
    parser.add_argument(
        "--send-only", action="store_true", help=_("仅发送最新的EPUB，不生成新的")
    )
    args = parser.parse_args()

    if not args.send_only:
        # 生成EPUB
        print(_("分隔符"))
        print(_("📖 开始生成EPUB..."))
        print(_("分隔符"))
        generate_epub()
        print(_("✅ EPUB生成成功！"))

    if not args.no_send:
        # 发送到Kindle
        print("\n" + _("分隔符"))
        print(_("📧 准备发送到Kindle..."))
        print(_("分隔符"))

        # 加载邮件配置
        config = load_email_config()
        if not config:
            print(_("⚠️ 跳过邮件发送（配置文件未找到）"))
            print(_("   提示：创建 email_config.yaml 来启用邮件发送功能"))
            return 0

        # 获取最新的EPUB文件
        epub_file = get_latest_epub()
        if not epub_file:
            print(_("❌ 没有找到EPUB文件可以发送"))
            return 1

        # 发送邮件
        if send_to_kindle(epub_file, config):
            print("\n" + _("分隔符"))
            print(_("🎉 完成！EPUB已生成并发送到Kindle"))
            print(_("分隔符"))
            return 0
        else:
            print(_("⚠️ EPUB已生成但邮件发送失败"))
            return 1

    print("\n" + _("分隔符"))
    print(_("✅ EPUB生成完成（未发送邮件）"))
    print(_("分隔符"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
