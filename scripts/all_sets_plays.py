# all_sets_plays.py
# Reads all-sets.md, fetches play counts from Mixcloud, SoundCloud, and YouTube,
# then updates the play counts in all-sets.md in place.
#
# Usage:
#   python scripts/all_sets_plays.py          # update all-sets.md with fresh play counts
#   python scripts/all_sets_plays.py sort     # print all-sets.md entries sorted by plays (stdout)
#
# Environment variables:
#   SOUNDCLOUD_OAUTH_TOKEN   – manually obtained SoundCloud OAuth 2.1 access token (optional)
#   SOUNDCLOUD_CLIENT_ID     – SoundCloud app client_id (optional)
#   SOUNDCLOUD_CLIENT_SECRET – SoundCloud app client_secret (optional)
#   YOUTUBE_API_KEY          – Google/YouTube Data API v3 key (required for YouTube plays)
#
# SoundCloud authentication (OAuth 2.1, required for API access):
#   Guide:       https://developers.soundcloud.com/docs/api/guide#authentication
#   Auth URL:    https://secure.soundcloud.com
#   Token URL:   https://secure.soundcloud.com/oauth/token
#   Method:      Client Credentials — credentials via Authorization: Basic header (NOT request body)
#   Rate limits: 30 tokens/hour/IP · 50 tokens/12h/app
#   Migration:   https://developers.soundcloud.com/blog/oauth-migration
#
# If the Client Credentials token exchange fails (e.g. rate-limited), the script
# automatically falls back to HTML scraping of soundcloud.com track pages.

import os
import re
import sys
import json
import time
import base64
import urllib.parse
import urllib.request

# Ensure stdout/stderr use UTF-8 (needed on Windows where default may be cp1250)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALL_SETS_MD = os.path.join(SCRIPT_DIR, "..", "all-sets.md")
ALL_SETS_SORTED_MD = os.path.join(SCRIPT_DIR, "..", "all-sets-sorted.md")

debug_on = True

# Cached SoundCloud OAuth token (obtained once per run)
_sc_token_cache = None
_sc_token_fetched = False   # True once we attempted (even if it failed)


def _retry_urlopen(req_or_url, retries=3, base_delay=2):
    """urllib.request.urlopen with automatic retry on HTTP 429 (rate limit)."""
    delay = base_delay
    last_exc = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req_or_url)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                last_exc = e
                debug_log(
                    "[WARN] Rate limited (429), retrying in %ds (attempt %d/%d)...\n",
                    delay, attempt + 1, retries,
                )
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc


def _get_sc_oauth_token():
    """Obtain a SoundCloud OAuth token via client credentials (cached for the run)."""
    global _sc_token_cache, _sc_token_fetched
    if _sc_token_fetched:
        return _sc_token_cache  # None if previously failed, string if succeeded
    _sc_token_fetched = True    # mark as attempted regardless of outcome
    client_id = os.environ.get("SOUNDCLOUD_CLIENT_ID", "")
    client_secret = os.environ.get("SOUNDCLOUD_CLIENT_SECRET", "")
    if not (client_id and client_secret):
        debug_log("[ERROR] SOUNDCLOUD_CLIENT_ID or SOUNDCLOUD_CLIENT_SECRET not set, skipping token exchange\n")
        return None
    debug_log("[DEBUG] Requesting SoundCloud OAuth token (client credentials)...\n")
    token_url = "https://secure.soundcloud.com/oauth/token"
    # OAuth 2.1: credentials MUST be in Authorization: Basic header, not in body
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        token_url,
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with _retry_urlopen(req, retries=1) as resp:  # no retry: 429 = IP is rate-limited for the window
            tok = json.load(resp)
            access_token = tok.get("access_token", "")
            if access_token:
                debug_log("[DEBUG] Obtained SoundCloud OAuth token (cached for this run)\n")
                _sc_token_cache = access_token
                return access_token
    except Exception as e:
        debug_log("[DEBUG] Token exchange error: %s\n", e)
    debug_log("[WARN] SoundCloud token exchange failed — skipping API for remaining sets\n")
    return None


def debug_log(fmt, *args):
    if debug_on:
        print(fmt % args, end="", file=sys.stderr)


def fetch_url(url):
    debug_log("[DEBUG] Fetching URL: %s\n", url)
    try:
        with urllib.request.urlopen(url) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        debug_log("[DEBUG] Fetched %d bytes from %s\n", len(body), url)
        return body
    except Exception as e:
        debug_log("[DEBUG] Error fetching URL %s: %v\n", url, e)
        return None


def extract_set_links(filename):
    """Parse all-sets.md and return (names, links, raw_lines).
    Non-linked list items get an empty string as link."""
    debug_log("[DEBUG] Opening file: %s\n", filename)
    re_link = re.compile(r"\* \[(.*?)\]\((.*?)\)")
    names = []
    links = []
    raw_lines = []
    seen = set()
    with open(filename, encoding="utf-8") as f:
        for line in f:
            trim = line.strip()
            if not trim.startswith("* "):
                continue
            m = re_link.match(trim)
            if m:
                name, link = m.group(1), m.group(2)
                key = link if link else trim
                if key in seen:
                    continue
                seen.add(key)
                debug_log("[DEBUG] Found set (linked): %s (%s)\n", name, link)
                names.append(name)
                links.append(link)
                raw_lines.append(trim)
            else:
                key = trim
                if key in seen:
                    continue
                seen.add(key)
                debug_log("[DEBUG] Found set (unlinked/raw): %s\n", trim)
                names.append(trim)
                links.append("")
                raw_lines.append(trim)
    debug_log("[DEBUG] Extracted %d unique sets (including unlinked)\n", len(names))
    return names, links, raw_lines


def get_mixcloud_plays(mixcloud_url):
    debug_log("[DEBUG] getMixcloudPlays called with URL: %s\n", mixcloud_url)
    m = re.search(r"https://www\.mixcloud\.com/([^/]+)/([^/?#]+)/?", mixcloud_url)
    if not m:
        debug_log("[DEBUG] Could not parse Mixcloud URL: %s\n", mixcloud_url)
        return 0
    username = urllib.parse.quote(m.group(1))
    slug = urllib.parse.quote(m.group(2))
    api_url = f"https://api.mixcloud.com/{username}/{slug}/"
    debug_log("[DEBUG] Fetching Mixcloud API URL: %s\n", api_url)
    try:
        with urllib.request.urlopen(api_url) as resp:
            if resp.status != 200:
                debug_log("[DEBUG] Mixcloud API returned status: %d\n", resp.status)
                return 0
            data = json.load(resp)
        play_count = data.get("play_count", 0)
        debug_log("[DEBUG] Mixcloud play_count: %d\n", play_count)
        return play_count
    except Exception as e:
        debug_log("[DEBUG] Error fetching Mixcloud API: %s\n", e)
        return 0


def resolve_soundcloud_with_token(sc_url, token):
    """Resolve a SoundCloud URL using an OAuth token. Returns (plays, ok)."""
    sc_url = sc_url.rstrip("/")  # trailing slash causes 404 on resolve
    resolve_api = "https://api.soundcloud.com/resolve?url=" + urllib.parse.quote(sc_url, safe="")
    req = urllib.request.Request(resolve_api, headers={"Authorization": "OAuth " + token})
    try:
        with _retry_urlopen(req) as resp:
            if resp.status == 200:
                data = json.load(resp)
                plays = data.get("playback_count", 0)
                debug_log("[DEBUG] SoundCloud playback_count (API OAuth): %d\n", plays)
                return plays, True
    except urllib.error.HTTPError as e:
        debug_log("[DEBUG] SoundCloud resolve with token returned status: %d\n", e.code)
    except Exception as e:
        debug_log("[DEBUG] Error resolving SoundCloud URL with token: %s\n", e)
    return 0, False


def get_soundcloud_plays(sc_url):
    debug_log("[DEBUG] getSoundcloudPlays called with URL: %s\n", sc_url)
    sc_url = sc_url.rstrip("/")  # normalize: strip trailing slash
    time.sleep(0.5)  # proactive delay to avoid rate limiting

    # 1) Prefer explicit OAuth token in env
    oauth_token = os.environ.get("SOUNDCLOUD_OAUTH_TOKEN", "")
    if oauth_token:
        debug_log("[DEBUG] Using SOUNDCLOUD_OAUTH_TOKEN\n")
        plays, ok = resolve_soundcloud_with_token(sc_url, oauth_token)
        if ok:
            return plays
        debug_log("[WARN] SoundCloud OAuth token request failed, will try other methods\n")

    # 2) Try cached/obtained token from client credentials (token fetched only once)
    token = _get_sc_oauth_token()
    if token:
        plays, ok = resolve_soundcloud_with_token(sc_url, token)
        if ok:
            return plays
        debug_log("[WARN] SoundCloud resolve with obtained token failed\n")

    # 3) HTML fallback: try to extract playback_count from page source
    debug_log("[DEBUG] Fetching SoundCloud page for HTML fallback: %s\n", sc_url)
    try:
        with urllib.request.urlopen(sc_url) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        for pattern in [r'"playback_count"\s*:\s*([0-9]+)', r'playback_count\s*:\s*([0-9]+)']:
            m = re.search(pattern, body)
            if m:
                plays = int(m.group(1))
                debug_log("[DEBUG] SoundCloud playback_count (HTML fallback): %d\n", plays)
                return plays
    except Exception as e:
        debug_log("[DEBUG] Error fetching SoundCloud page: %s\n", e)

    debug_log("[WARN] Could not determine SoundCloud playback_count for %s\n", sc_url)
    return 0


def get_youtube_plays(yt_url):
    debug_log("[DEBUG] getYouTubePlays called with URL: %s\n", yt_url)
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        debug_log("[WARN] YouTube API key not set in environment. Skipping.\n")
        return 0

    video_id = None
    m = re.search(r"youtube\.com/(?:watch\?v=|live/)([a-zA-Z0-9_-]+)", yt_url)
    if m:
        video_id = m.group(1)
    else:
        m = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", yt_url)
        if m:
            video_id = m.group(1)

    if not video_id:
        debug_log("[DEBUG] Could not extract YouTube video ID from URL: %s\n", yt_url)
        return 0

    api_url = (
        f"https://www.googleapis.com/youtube/v3/videos"
        f"?part=statistics&id={video_id}&key={api_key}"
    )
    debug_log("[DEBUG] Fetching YouTube API URL: %s\n", api_url)
    try:
        with urllib.request.urlopen(api_url) as resp:
            if resp.status != 200:
                debug_log("[DEBUG] YouTube API returned status: %d\n", resp.status)
                return 0
            data = json.load(resp)
        items = data.get("items", [])
        if not items:
            debug_log("[DEBUG] No items found for video ID: %s\n", video_id)
            return 0
        view_count = int(items[0]["statistics"]["viewCount"])
        debug_log("[DEBUG] YouTube viewCount: %d\n", view_count)
        return view_count
    except Exception as e:
        debug_log("[DEBUG] Error fetching YouTube API: %s\n", e)
        return 0


def find_external_links(page):
    mixcloud = soundcloud = youtube = ""
    m = re.search(r'https://www\.mixcloud\.com/[^"]+', page)
    if m:
        mixcloud = m.group(0)
        debug_log("[DEBUG] Found Mixcloud link: %s\n", mixcloud)
    m = re.search(r'https://soundcloud\.com/[^"]+', page)
    if m:
        soundcloud = m.group(0)
    m = re.search(r'https://(?:www\.)?youtube\.com/[^"]+|https://youtu\.be/[^"]+', page)
    if m:
        youtube = m.group(0)
    debug_log(
        "[DEBUG] External links found - Mixcloud: %s, SoundCloud: %s, YouTube: %s\n",
        mixcloud, soundcloud, youtube,
    )
    return mixcloud, soundcloud, youtube


def format_plays(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def update_all_sets_sorted_md(total_plays, total_sets):
    """Read updated all-sets.md, sort entries by plays descending, write all-sets-sorted.md."""
    re_plays = re.compile(r"([0-9]+)\U0001f3a7")
    re_link = re.compile(r"\((https?://[^\s)]+)\)")

    with open(ALL_SETS_MD, encoding="utf-8") as f:
        lines = f.read().splitlines()

    entries = []
    seen_links = set()
    for ln in lines:
        trim = ln.strip()
        if not trim.startswith("* "):
            continue
        link = ""
        m = re_link.search(trim)
        if m:
            link = m.group(1)
        if link and link in seen_links:
            continue
        plays = 0
        m = re_plays.search(trim)
        if m:
            plays = int(m.group(1))
        entries.append({"line": trim, "plays": plays, "link": link})
        if link:
            seen_links.add(link)

    entries.sort(key=lambda e: e["plays"], reverse=True)

    with open(ALL_SETS_SORTED_MD, "w", encoding="utf-8") as f:
        f.write("![Shivioua - All Sets](./all-sets.jpg)\n\n")
        f.write("# All Sets (DJ Mixes)\n\n")
        f.write("Order by - [Newest](./all-sets.md) :: **[Top Listens](./all-sets-sorted.md)**\n\n")
        for e in entries:
            f.write(e["line"] + "\n")
        f.write(f"\nTotal plays: **{format_plays(total_plays)}\U0001f3a7**  \n")
        f.write(f"Total amount of sets: **{total_sets}\U0001f3b6**  \n")
        f.write("\nThank you for listening \U0001f60d\n\n")
        f.write("----\n\n")
        f.write("[Back to main page](https://shivioua.github.io)\n\n")
        f.write("----\n")

    debug_log("[DEBUG] Updated %s\n", ALL_SETS_SORTED_MD)


def main():
    debug_log("[DEBUG] Starting all_sets_plays.py\n")

    re_set_entry = re.compile(r"^\* \[(.+?)\]\((https?://[^\s)]+)\)")

    with open(ALL_SETS_MD, encoding="utf-8") as f:
        lines = f.readlines()

    total_plays = 0
    total_sets = 0
    processed = set()
    new_lines = []

    for line in lines:
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped):]

        m = re_set_entry.match(stripped)
        if m:
            name = m.group(1)
            link = m.group(2)

            if link in processed:
                new_lines.append(line)
                continue
            processed.add(link)
            total_sets += 1

            page = fetch_url(link)
            plays = 0
            if page:
                mixcloud, soundcloud, youtube = find_external_links(page)
                if mixcloud:
                    plays += get_mixcloud_plays(mixcloud)
                if soundcloud:
                    plays += get_soundcloud_plays(soundcloud)
                if youtube:
                    plays += get_youtube_plays(youtube)

            total_plays += plays
            if plays > 0:
                new_lines.append(f"* [{name}]({link}) _//_ {plays}🎧{ending}")
            else:
                new_lines.append(f"* [{name}]({link}){ending}")
        elif re.match(r"^Total plays:", stripped):
            new_lines.append(f"Total plays: **{format_plays(total_plays)}🎧**  {ending}")
        elif re.match(r"^Total amount of sets:", stripped):
            new_lines.append(f"Total amount of sets: **{total_sets}🎶**  {ending}")
        else:
            new_lines.append(line)

    with open(ALL_SETS_MD, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    update_all_sets_sorted_md(total_plays, total_sets)

    print(f"Zaktualizowano: {ALL_SETS_MD}")
    print(f"Zaktualizowano: {ALL_SETS_SORTED_MD}")
    print(f"Total plays: {format_plays(total_plays)}🎧, Total sets: {total_sets}🎶")


if __name__ == "__main__":
    main()
