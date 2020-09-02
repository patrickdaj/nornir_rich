from rich.highlighter import RegexHighlighter

class NornirHighlighter(RegexHighlighter):
    """Highlights the text typically produced from ``__repr__`` methods."""

    base_style = "repr."
    highlights = [
        r"(?P<str>\"[\w\-\.]*\"^:)",
        r"(?P<str>\'[\w\-\.]*\'^:)",
        r"(?P<brace>[\{\[\(\)\]\}])",
        r"(?P<attrib_name>\"[\w\-\.]*\") ?\: ?",
        r"(?P<attrib_name>[\w\-\.]*) ?\: ?",
        r"(?P<diff_add>\+.*)\n",
        r"(?P<diff_rm>\-.*)\n",
        #r"(?P<tag_start>\<\/)(?P<tag_name>[\w\-\.]*)(?P<tag_end>\>)",
        #r"(?P<tag_start>\<)(?P<tag_name>[\w\-\.]*)(?P<tag_contents>.*?)(?P<tag_end>\/?\>)",
        #r"(?P<attrib_name>\w+?)=(?P<attrib_value>\"?[\w_]+\"?)",
        r"(?P<bool_true>True)|(?P<bool_false>False)|(?P<none>None)",
        r"(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[\-\+]?\d+?)?\b)",
        r"(?P<number>0x[0-9a-f]*)",
        #r"(?P<path>\B(\/[\w\.\-\_\+]+)*\/)(?P<filename>[\w\.\-\_\+]*)?",
        #r"(?<!\\)(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
        #r"(?P<url>https?:\/\/[0-9a-zA-Z\$\-\_\+\!`\(\)\,\.\?\/\;\:\&\=\%]*)",
        #r"(?P<uuid>[a-fA-F0-9]{8}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{12})",
    ]