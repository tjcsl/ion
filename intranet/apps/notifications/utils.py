def truncate_content(content: str) -> str:
    if len(content) > 200:
        return content[:200] + "..."
    return content


def truncate_title(title: str) -> str:
    if len(title) > 50:
        return title[:50] + "..."
    return title
