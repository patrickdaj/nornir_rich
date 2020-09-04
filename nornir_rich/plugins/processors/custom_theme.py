from rich.theme import Theme
from rich.style import Style
from rich.default_styles import DEFAULT_STYLES

# any defaults can be re-mapped here
# for reference https://github.com/willmcgugan/rich/blob/master/rich/default_styles.py

CustomTheme = Theme(
    {
        **DEFAULT_STYLES,
        "progress.percentage": Style(color="blue"),
        "host": Style(color="blue"),
        "failed": Style(color="red"),
        "changed": Style(color="orange1"),
        "ok": Style(color="dark_green"),
        "no_style": Style(),
        "skipped": Style(color="grey50"),
        "params": Style(color="grey50"),
    }
)
