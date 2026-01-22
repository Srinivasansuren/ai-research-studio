from bs4 import BeautifulSoup


def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    lines = [ln.strip() for ln in text.splitlines()]
    out = []
    prev_blank = False

    for ln in lines:
        if not ln:
            if not prev_blank:
                out.append("")
            prev_blank = True
        else:
            out.append(ln)
            prev_blank = False

    return "\n".join(out).strip() + "\n"
