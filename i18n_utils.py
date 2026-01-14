#!/usr/bin/env python3
"""
Internationalization (i18n) utility using Python's built-in gettext
Supports multiple languages with fallback to English
"""

import gettext
import locale
import os
from pathlib import Path
from typing import Optional


class I18nManager:
    """Manages internationalization using Python's gettext"""

    def __init__(self, domain: str = "kindle_rss", localedir: Optional[str] = None):
        self.domain = domain
        self.localedir = localedir or str(Path(__file__).parent / "locale")
        self.current_language = None
        self._translation = None

        # Initialize with system locale
        self._detect_and_set_language()

    def _detect_and_set_language(self):
        """Auto-detect language from environment variables"""
        # Check specific environment variable first
        lang = os.environ.get("KINDLE_RSS_LANG")
        if lang:
            self.set_language(lang)
            return

        # Try system locale
        try:
            system_locale, _ = locale.getdefaultlocale()
            if system_locale:
                # Convert system locale to our format
                if system_locale.startswith("zh"):
                    self.set_language("zh_CN")
                elif system_locale.startswith("en"):
                    self.set_language("en_US")
                else:
                    self.set_language("en_US")  # Default fallback
            else:
                self.set_language("en_US")
        except Exception:
            self.set_language("en_US")  # Safe fallback

    def set_language(self, language: str):
        """Set the current language and load translations"""
        self.current_language = language

        try:
            # Try to load the specific translation
            self._translation = gettext.translation(
                self.domain,
                localedir=self.localedir,
                languages=[language],
                fallback=True,
            )
            print(f"Loaded language: {language}")
        except Exception as e:
            print(f"Warning: Could not load language '{language}': {e}")
            # Fall back to English
            try:
                self._translation = gettext.translation(
                    self.domain,
                    localedir=self.localedir,
                    languages=["en_US"],
                    fallback=True,
                )
                self.current_language = "en_US"
            except Exception:
                # Ultimate fallback - use NullTranslations
                self._translation = gettext.NullTranslations()
                self.current_language = "en_US"

    def get_current_language(self) -> str:
        """Get the current language code"""
        return self.current_language or "en_US"

    def _(self, message: str) -> str:
        """Translate a message (gettext standard function name)"""
        if self._translation:
            return self._translation.gettext(message)
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Handle plural forms"""
        if self._translation:
            return self._translation.ngettext(singular, plural, n)
        return singular if n == 1 else plural


# Global instance
_i18n_manager = None


def init_i18n(language: Optional[str] = None) -> I18nManager:
    """Initialize the global i18n manager"""
    global _i18n_manager
    _i18n_manager = I18nManager()
    if language:
        _i18n_manager.set_language(language)
    return _i18n_manager


def get_i18n_manager() -> I18nManager:
    """Get the global i18n manager, initializing if needed"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def _(message: str) -> str:
    """
    Global translation function
    This is the standard gettext function name for translations
    """
    return get_i18n_manager()._(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Global plural translation function"""
    return get_i18n_manager().ngettext(singular, plural, n)


def set_language(language: str):
    """Set the global language"""
    get_i18n_manager().set_language(language)


def get_current_language() -> str:
    """Get the current language"""
    return get_i18n_manager().get_current_language()


# Convenience aliases
t = _  # Common alias for translation function
