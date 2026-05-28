#!/usr/bin/env python3
"""Submit all indexable URLs to IndexNow for rapid re-crawling.

Reads sitemap.xml and submits URLs in batches of 100 to IndexNow API.
Uses the existing IndexNow key from the site root.
"""
import os
import re
import json
import urllib.request
import urllib.error
import time

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = 'gadurarealestate.com'
INDEXNOW_ENDPOINT = 'https://api.indexnow.org/indexnow'


def get_key():
    """Find the IndexNow key file."""
    for f in os.listdir(SITE_ROOT):
        if f.endswith('.txt') and len(f) == 36:  # UUID-like key file
            key = f.replace('.txt', '')
            if len(key) == 32:
                return key
    # Check for key in known files
    key_file = os.path.join(SITE_ROOT, '01c45d7d59fe16a687fe018d82ac8a04.txt')
    if os.path.exists(key_file):
        return '01c45d7d59fe16a687fe018d82ac8a04'
    return None


def parse_sitemap():
    """Extract URLs from sitemap.xml."""
    sitemap = os.path.join(SITE_ROOT, 'sitemap.xml')
    with open(sitemap, 'r') as f:
        content = f.read()
    return re.findall(r'<loc>(.*?)</loc>', content)


def submit_batch(urls, key):
    """Submit a batch of URLs to IndexNow."""
    payload = {
        'host': DOMAIN,
        'key': key,
        'keyLocation': f'https://{DOMAIN}/{key}.txt',
        'urlList': urls
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        response = urllib.request.urlopen(req, timeout=30)
        return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)


def main():
    key = get_key()
    if not key:
        print("ERROR: No IndexNow key found")
        return

    print(f"IndexNow key: {key}")

    urls = parse_sitemap()
    print(f"Total URLs from sitemap: {len(urls)}")

    batch_size = 100
    success = 0
    failed = 0

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(urls) + batch_size - 1) // batch_size

        status = submit_batch(batch, key)
        if status in (200, 202):
            success += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} URLs submitted (HTTP {status})")
        else:
            failed += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: FAILED (HTTP {status})")

        # Rate limit
        if i + batch_size < len(urls):
            time.sleep(1)

    print(f"\n=== INDEXNOW SUBMISSION COMPLETE ===")
    print(f"Submitted: {success}")
    print(f"Failed: {failed}")


if __name__ == '__main__':
    main()
