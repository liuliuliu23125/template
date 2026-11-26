import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

DEFAULT_PROFILE = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    / "TencentDocReader"
    / "profile"
)
DEFAULT_VIEWPORT = {"width": 1440, "height": 1000}
BLOCK_TAGS = {
    "p", "div", "section", "article", "body", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "ul", "ol", "blockquote", "pre",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="读取腾讯文档 /doc/ 页面：优先取剪贴板全文与图片，失败时回退滚动截图"
    )
    parser.add_argument("url", help="腾讯文档地址，例如 https://docs.qq.com/doc/XXXX")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE), help="Chrome 持久化配置目录")
    parser.add_argument("--login", action="store_true", help="打开有头浏览器，等待登录后继续")
    parser.add_argument("--headed", action="store_true", help="打开有头浏览器，不等待登录")
    parser.add_argument("--login-timeout", type=int, default=180, help="登录等待秒数")
    parser.add_argument("--wait", type=float, default=8.0, help="首次加载等待秒数")
    parser.add_argument("--mode", choices=("auto", "clipboard", "screenshot"), default="auto")
    parser.add_argument("--step", type=int, default=800, help="截图模式每次滚动的像素")
    parser.add_argument("--overlap", type=int, default=80, help="截图模式相邻截图重叠像素")
    parser.add_argument("--max-pages", type=int, default=80, help="截图模式最多截图张数")
    parser.add_argument("--render-wait", type=int, default=650, help="截图模式滚动后等待毫秒")
    parser.add_argument("--keep-html", action="store_true", help="额外保存剪贴板 HTML")
    return parser.parse_args()


def launch(p, args):
    headless = not (args.login or args.headed)
    kwargs = {
        "user_data_dir": args.profile,
        "headless": headless,
        "viewport": DEFAULT_VIEWPORT,
        "locale": "zh-CN",
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    try:
        return p.chromium.launch_persistent_context(channel="chrome", **kwargs)
    except PlaywrightError:
        return p.chromium.launch_persistent_context(**kwargs)


def scroll_info(page):
    return page.evaluate(
        """() => {
          const s = document.getElementById('scrollable');
          if (!s) return null;
          const z = s.querySelector('[class*="zoomable--"]');
          const sr = s.getBoundingClientRect();
          const zr = z ? z.getBoundingClientRect() : sr;
          return {
            scrollHeight: s.scrollHeight,
            clientHeight: s.clientHeight,
            scrollTop: s.scrollTop,
            clip: {x: zr.x, y: sr.y, width: zr.width, height: sr.height}
          };
        }"""
    )


def scroll_to(page, top):
    page.evaluate(
        "(top) => { const s = document.getElementById('scrollable'); if (s) s.scrollTop = top; }",
        top,
    )


def body_text(page):
    try:
        return page.inner_text("body")
    except PlaywrightError:
        return ""


LOGIN_MARKERS = (
    "登录腾讯文档",
    "登录后",
    "只能查看",
    "正在同步内容",
    "请登录",
)


def is_ready(page):
    text = body_text(page)
    if any(marker in text for marker in LOGIN_MARKERS):
        return False
    if len(text) < 100:
        return False
    return bool(re.search(r"[一-鿿]", text))


def wait_for_document(page, args):
    if args.login:
        print("请在打开的 Chrome 中登录腾讯文档，脚本会自动继续...", flush=True)
    deadline = time.time() + (args.login_timeout if args.login else 30)
    while time.time() < deadline:
        if is_ready(page):
            return True
        page.wait_for_timeout(2000)
    return is_ready(page)


def extract_title(page):
    title = (page.title() or "").strip()
    for suffix in (" - 腾讯文档", "-腾讯文档", " - Tencent Docs", "- Tencent Docs"):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()
    return title or "腾讯文档"


def extract_char_count(text):
    match = re.search(r"(\d[\d,]*)\s*个字", text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def outline_from_body(text):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^([一二三四五六七八九十]+[、.]|\d+[、.]|\d+\.\s*)", line):
            lines.append(line)
    return lines


def clean_inline(text):
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace(" ", " ")
    return text.strip()


def inline_text(el):
    parts = []
    for child in el.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name in ("style", "script"):
                continue
            if child.name == "o:p":
                if child.get_text(strip=True):
                    parts.append(child.get_text())
                continue
            if child.name == "br":
                parts.append("\n")
            elif child.name == "img":
                src = child.get("src", "")
                if src:
                    parts.append(f"\n\n![image]({src})\n\n")
            else:
                parts.append(inline_text(child))
    return "".join(parts)


def cell_text(cell):
    text = clean_inline(inline_text(cell))
    text = re.sub(r"\n+", " ", text).strip()
    return text.replace("|", "\\|")


def render_table(table):
    lines = []
    for row_index, row in enumerate(table.find_all("tr")):
        values = []
        for cell in row.find_all(["td", "th"], recursive=False):
            values.append(cell_text(cell))
            span = int(cell.get("colspan", "1") or "1")
            values.extend([""] * (span - 1))
        if not values:
            continue
        lines.append("| " + " | ".join(values) + " |")
        if row_index == 0:
            lines.append("| " + " | ".join(["---"] * len(values)) + " |")
    return "\n".join(lines)


def render_list(el):
    lines = []
    ordered = el.name == "ol"
    for index, li in enumerate(el.find_all("li", recursive=False), start=1):
        text = clean_inline(inline_text(li))
        text = re.sub(r"\n+", " ", text).strip()
        if text:
            lines.append((f"{index}. " if ordered else "- ") + text)
    return "\n".join(lines)


def heading_level(text, is_first):
    if is_first and len(text) <= 40 and "\n" not in text:
        return 1
    if re.match(r"^[一二三四五六七八九十]+[、.]", text):
        return 2
    if re.match(r"^\d+[、.]", text) or re.match(r"^\d+\.\s", text):
        return 3
    return 0


def render_element(el, is_first):
    if isinstance(el, NavigableString):
        return clean_inline(str(el))
    if not isinstance(el, Tag):
        return ""
    if el.name in ("style", "script"):
        return ""
    if el.name == "img":
        src = el.get("src", "")
        return f"![image]({src})" if src else ""
    if el.name == "table":
        return render_table(el)
    if el.name in ("ul", "ol"):
        return render_list(el)
    if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = clean_inline(inline_text(el))
        return "#" * int(el.name[1]) + " " + text if text else ""
    if el.name == "p":
        text = clean_inline(inline_text(el))
        if not text:
            return ""
        if text.startswith("![image]") and text.endswith(")"):
            return text
        level = heading_level(text, is_first)
        return "#" * level + " " + text if level else text
    if el.name in ("div", "section", "article", "body"):
        parts = []
        for child in el.children:
            if isinstance(child, NavigableString):
                text = clean_inline(str(child))
                if text:
                    parts.append(text)
            elif isinstance(child, Tag):
                if child.name in BLOCK_TAGS or child.name in ("img",):
                    rendered = render_element(child, False)
                else:
                    rendered = clean_inline(inline_text(child))
                if rendered.strip():
                    parts.append(rendered.strip())
        return "\n\n".join(parts)
    return clean_inline(inline_text(el))


def html_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["style", "script"]):
        tag.decompose()
    root = soup.body or soup
    blocks = []
    first_content = True
    for child in root.children:
        if isinstance(child, Tag):
            if child.name in BLOCK_TAGS or child.name == "img":
                rendered = render_element(child, first_content)
                if rendered.strip():
                    blocks.append(rendered.strip())
                    first_content = False
        elif isinstance(child, NavigableString):
            text = clean_inline(str(child))
            if text:
                blocks.append(text)
                first_content = False
    if blocks and not blocks[0].startswith("#") and len(blocks[0]) <= 40 and "\n" not in blocks[0]:
        blocks[0] = "# " + blocks[0]
    md = "\n\n".join(blocks)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    lines = md.splitlines()
    if lines and lines[0].strip() and not lines[0].startswith("#") and not lines[0].startswith("!["):
        lines[0] = "# " + lines[0].strip()
    md = "\n".join(lines)
    return md, len(soup.find_all("table"))


def save_data_images(html, out_dir):
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    count = [0]

    def replace(match):
        mime = match.group(1)
        payload = match.group(2)
        ext = "jpg" if mime in ("jpeg", "jpg") else mime
        if ext == "svg+xml":
            ext = "svg"
        count[0] += 1
        name = f"image-{count[0]:02d}.{ext}"
        try:
            (img_dir / name).write_bytes(base64.b64decode(payload))
        except Exception:
            return match.group(0)
        return f'src="images/{name}"'

    html = re.sub(r'src="data:image/([^;"]+);base64,([^"]+)"', replace, html)
    return html, count[0]


def extract_clipboard_html(html):
    html = re.sub(r'\s+tdoc-data-src="[^"]*"', "", html, flags=re.S)
    html = re.sub(r'\s+thumb="[^"]*"', "", html)
    return html


def read_clipboard(page):
    return page.evaluate(
        """async () => {
          const out = {text: '', html: '', error: null, htmlError: null};
          try { out.text = await navigator.clipboard.readText(); } catch (e) { out.error = String(e); }
          try {
            const items = await navigator.clipboard.read();
            for (const item of items) {
              for (const type of item.types) {
                if (type === 'text/html') {
                  const blob = await item.getType(type);
                  out.html = await blob.text();
                }
              }
            }
          } catch (e) { out.htmlError = String(e); }
          return out;
        }"""
    )


def copy_document(page, context, url):
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    try:
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
    except PlaywrightError:
        pass
    info = scroll_info(page)
    if info:
        clip = info["clip"]
        page.mouse.click(clip["x"] + clip["width"] / 2, clip["y"] + 200)
        page.wait_for_timeout(300)
    page.keyboard.press("Control+A")
    page.wait_for_timeout(300)
    page.keyboard.press("Control+C")
    page.wait_for_timeout(1200)
    return read_clipboard(page)


def cleanup_partial(out):
    for name in ("document.txt", "document.md", "clipboard.html", "meta.json"):
        (out / name).unlink(missing_ok=True)
    shutil.rmtree(out / "images", ignore_errors=True)


def capture_clipboard(page, context, args, out, title, body, outline, char_count):
    result = copy_document(page, context, args.url)
    text = result.get("text") or ""
    html = result.get("html") or ""
    if len(text) < 200:
        print(f"剪贴板文本过短: {len(text)} 字符", file=sys.stderr)
        return None
    if not re.search(r"[一-鿿]", text):
        print("剪贴板文本不含中文", file=sys.stderr)
        return None
    if char_count and len(text) < char_count * 0.5:
        print(f"剪贴板文本可能不完整: {len(text)} / {char_count} 字", file=sys.stderr)
        return None

    html = extract_clipboard_html(html)
    image_tags = len(re.findall(r"<img\b", html, flags=re.I))
    html, image_count = save_data_images(html, out)
    md, table_count = html_to_markdown(html)
    reasons = []
    if char_count and len(text) < char_count * 0.9:
        reasons.append(f"文本 {len(text)} 少于页面字数 {char_count} 的 90%")
    if image_tags and image_count < image_tags:
        reasons.append(f"图片仅提取 {image_count}/{image_tags} 张")
    if len(md) < 500:
        reasons.append(f"Markdown 过短: {len(md)} 字符")
    if reasons:
        print("读取不完整: " + "; ".join(reasons), file=sys.stderr)
        cleanup_partial(out)
        return None

    (out / "document.txt").write_text(text, encoding="utf-8")
    (out / "document.md").write_text(md, encoding="utf-8")
    if args.keep_html:
        (out / "clipboard.html").write_text(html, encoding="utf-8")

    meta = {
        "method": "clipboard",
        "url": args.url,
        "title": title,
        "char_count": char_count,
        "text_chars": len(text),
        "markdown_chars": len(md),
        "image_count": image_count,
        "image_tags": image_tags,
        "table_count": table_count,
        "outline": outline,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "truncated": False,
        "complete": True,
        "truncated_reasons": [],
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "markdown_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"标题: {title}")
    print(f"字数: {char_count if char_count is not None else '未知'}")
    print(f"文本: {len(text)} 字符 -> {out / 'document.txt'}")
    print(f"Markdown: {len(md)} 字符, 表格 {table_count} -> {out / 'document.md'}")
    print(f"图片: {image_count}/{image_tags} 张 -> {out / 'images'}")
    return meta


def capture_screenshots(page, args, out, title, body, outline, char_count):
    info = scroll_info(page)
    if not info:
        print("未找到文档滚动容器。", file=sys.stderr)
        return None
    viewport = info["clientHeight"]
    step = args.step if args.step > 0 else viewport - args.overlap
    step = max(200, min(step, viewport - args.overlap))
    max_scroll = max(0, info["scrollHeight"] - viewport)

    pre_step = max(step * 3, 2000)
    pos = 0
    while pos < max_scroll:
        scroll_to(page, pos)
        page.wait_for_timeout(120)
        pos += pre_step
    scroll_to(page, max_scroll)
    page.wait_for_timeout(300)
    scroll_to(page, 0)
    page.wait_for_timeout(500)

    positions = list(range(0, max_scroll + 1, step))
    if not positions or positions[-1] != max_scroll:
        positions.append(max_scroll)
    truncated = len(positions) > args.max_pages
    positions = positions[: args.max_pages]
    if truncated:
        print("警告: 超过 --max-pages，后段未截取，需调大该参数重跑。", file=sys.stderr)

    pages = []
    for index, top in enumerate(positions, start=1):
        scroll_to(page, top)
        page.wait_for_timeout(args.render_wait)
        name = f"page-{index:03d}.png"
        clip = info["clip"]
        page.screenshot(
            path=str(out / name),
            clip={
                "x": round(clip["x"]),
                "y": round(clip["y"]),
                "width": round(clip["width"]),
                "height": round(clip["height"]),
            },
        )
        pages.append({"index": index, "scroll_top": top, "file": name})

    meta = {
        "method": "screenshot",
        "url": args.url,
        "title": title,
        "char_count": char_count,
        "outline": outline,
        "scroll_height": info["scrollHeight"],
        "client_height": viewport,
        "step": step,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "truncated": truncated,
        "complete": not truncated,
        "truncated_reasons": [] if not truncated else ["超过 --max-pages"],
        "pages": pages,
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"标题: {title}")
    print(f"字数: {char_count if char_count is not None else '未知'}")
    print(f"截图: {len(pages)} 张 -> {out}")
    return meta


def main():
    args = parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if "spec" in out.parts:
        print(
            "警告: reader 输出在 spec/ 下；spec 只保留指纹，请改用系统临时目录。",
            file=sys.stderr,
        )

    with sync_playwright() as p:
        context = launch(p, args)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        except PlaywrightError as exc:
            print(f"打开失败: {exc}", file=sys.stderr)
            context.close()
            return 2

        page.wait_for_timeout(int(args.wait * 1000))
        if not wait_for_document(page, args):
            print("未读到文档正文：可能需要登录，或链接不是 /doc/ 文档。", file=sys.stderr)
            print("可加 --login 重新运行，在打开的 Chrome 中登录后再继续。", file=sys.stderr)
            context.close()
            return 3

        title = extract_title(page)
        body = body_text(page)
        outline = outline_from_body(body)
        char_count = extract_char_count(body)

        if args.mode in ("auto", "clipboard"):
            meta = capture_clipboard(page, context, args, out, title, body, outline, char_count)
            if meta:
                context.close()
                return 0
            if args.mode == "clipboard":
                print("剪贴板读取失败；可用 --mode screenshot 回退。", file=sys.stderr)
                context.close()
                return 5
            print("剪贴板不可用，回退到滚动截图。", file=sys.stderr)

        if args.mode in ("auto", "screenshot"):
            meta = capture_screenshots(page, args, out, title, body, outline, char_count)
            context.close()
            return 0 if meta else 4

        context.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
