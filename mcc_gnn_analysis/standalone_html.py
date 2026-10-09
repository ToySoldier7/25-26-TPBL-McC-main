"""Embed local report images and figure downloads for single-file sharing."""
from pathlib import Path
import base64
import mimetypes
import re

def embed_images(content: str, root: Path):
    cache = {}
    def uri(relative):
        if relative not in cache:
            path = root / relative
            mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            cache[relative] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
        return cache[relative]
    count = 0
    def replace_image(match):
        nonlocal count
        source = match.group(2)
        if source.startswith(('data:', 'http:', 'https:')):
            return match.group(0)
        count += 1
        return match.group(1) + uri(source) + match.group(3)
    content = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")', replace_image, content)
    def replace_download(match):
        relative = match.group(2)
        if not relative.startswith('v2/figures/') or Path(relative).suffix.lower() not in {'.png', '.svg'}:
            return match.group(0)
        return match.group(1) + uri(relative) + '" download="' + Path(relative).name + match.group(3)
    content = re.sub(r'(<a\b[^>]*\bhref=")([^"]+)(")', replace_download, content)
    assert not re.search(r'<img\b[^>]*\bsrc="(?!data:)[^"]+"', content)
    return content, count
