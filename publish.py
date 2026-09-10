#!/usr/bin/env python3
"""huiguojiasuqi 文章 → GitHub 仓库发布
用法: python3 publish.py <数量> [--start N]   (从 _posts_index.tsv 顶部取)
"""
import csv, html2text, os, re, subprocess, sys, urllib.request, urllib.parse, html as htmllib

REPO = '/root/github-huiguojiasuqi'
SITE = 'https://huiguojiasuqi.com'
CAT_DIR = {'yingyin': 'yingyin-huiguo-yingyin', 'tiyu': 'tiyu-tiyu-zhibo',
           'yinyue': 'yinyue-yinyue-yinpin', 'duanju': 'duanju-duanju-zhibo',
           'bangong': 'bangong-bangong-baokao', 'youxi': 'youxi-huiguo-youxi',
           'jiaocheng': 'jiaocheng-shiyong-jiaocheng'}

h2t = html2text.HTML2Text()
h2t.body_width = 0          # 不强制换行
h2t.ignore_links = False
h2t.ignore_images = False
h2t.mark_code = True

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')

def extract(html):
    """取 <article class="article-body"> 或 <div class="entry"> 主体"""
    m = re.search(r'<div class="entry">(.*)</div>\s*</article>', html, re.S)
    if m:
        return m.group(1)
    m = re.search(r'<article[^>]*>(.*)</article>', html, re.S)
    return m.group(1) if m else None

def fix_links(md):
    # 相对链接 → 绝对；#锚点保留
    md = re.sub(r'\]\(/(?!/)', f']({SITE}/', md)
    # src="/wp-content → 绝对
    md = re.sub(r'src="(/(?!/))', f'src="{SITE}/', md)
    md = re.sub(r"\(/wp-content", f"({SITE}/wp-content", md)
    return md

def slugify(name_encoded):
    dec = urllib.parse.unquote(name_encoded)
    dec = htmllib.unescape(dec)
    dec = re.sub(r'[\\/:*?"<>|\s]+', '-', dec).strip('-')
    return dec[:80] or 'post'

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    start = 0
    if '--start' in sys.argv:
        start = int(sys.argv[sys.argv.index('--start') + 1])
    rows = []
    with open(f'{REPO}/_posts_index.tsv', encoding='utf-8') as f:
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 5:
                rows.append(p)
    batch = rows[start:start + n]
    ok, fail = 0, []
    for pid, cat, title, date, enc_slug in batch:
        try:
            url = f"{SITE}/{enc_slug}/"
            raw = fetch(url)
            body_html = extract(raw)
            if not body_html:
                fail.append((pid, 'no body'))
                continue
            md = h2t.handle(body_html).strip()
            md = fix_links(md)
            d = date[:10]
            catdir = CAT_DIR.get(cat, cat)
            fname = slugify(enc_slug)
            os.makedirs(f'{REPO}/posts/{catdir}', exist_ok=True)
            path = f'{REPO}/posts/{catdir}/{d}-{fname}.md'
            if os.path.exists(path):
                ok += 1
                continue
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"---\ntitle: \"{title}\"\ndate: {date}\ncategory: {cat}\n"
                        f"original: {url}\nlayout: post\n---\n\n{md}\n")
            ok += 1
            print(f'  {pid} -> {os.path.relpath(path, REPO)} ({len(md)} chars)')
        except Exception as e:
            fail.append((pid, str(e)[:100]))
    print(f'done: ok={ok} fail={len(fail)}')
    for pid, err in fail:
        print(f'  FAIL {pid}: {err}')

if __name__ == '__main__':
    main()
