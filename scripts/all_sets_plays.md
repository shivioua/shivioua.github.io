# `all_sets_plays.py`

Fetches play or view counts for the sets listed in `all-sets.md`, updates that file, and writes `all-sets-sorted.md` ordered by the recorded counts. The script discovers platform URLs from each set's linked page and sums the counts it can retrieve from Mixcloud, SoundCloud, and YouTube.

## Requirements

- Python 3.10 or later.
- Internet access to the Shivioua set pages and the relevant platform APIs/pages.
- A YouTube Data API v3 key for YouTube counts. SoundCloud API credentials or an OAuth token are optional; the script also attempts an HTML fallback.

The script uses only Python standard-library modules. It does not require a package installation.

## Usage

Run from the repository root:

```powershell
python scripts/all_sets_plays.py
```

The same invocation works from another working directory if the script path is correct. It always performs the update; there is no dry-run mode or supported `sort` subcommand. In particular, passing `sort` does not just sort locally: the script still fetches counts and writes both catalogue files.

## Configuration

Set credentials in the process environment before running:

| Variable                   | Required           | Purpose                                                                      |
|----------------------------|--------------------|------------------------------------------------------------------------------|
| `YOUTUBE_API_KEY`          | For YouTube counts | Google YouTube Data API v3 key. Without it, YouTube counts are skipped.      |
| `SOUNDCLOUD_OAUTH_TOKEN`   | No                 | Existing SoundCloud OAuth access token; tried first.                         |
| `SOUNDCLOUD_CLIENT_ID`     | No                 | SoundCloud application client ID used to request a client-credentials token. |
| `SOUNDCLOUD_CLIENT_SECRET` | No                 | SoundCloud application client secret. Used with the client ID.               |

Keep credentials out of Markdown, source files, and commits. When SoundCloud API authentication is unavailable, the script tries to read a playback count from the public SoundCloud page HTML; that fallback may stop working if the page markup changes.

## What It Updates

- `all-sets.md`: fetches each distinct linked set page, finds its Mixcloud, SoundCloud, and YouTube links, sums available platform counts, and rewrites the set entry and aggregate totals.
- `all-sets-sorted.md`: regenerates the top-listens view from the updated entries during the same run.

Duplicate set URLs are counted once. Totals are arithmetic sums across platforms, not deduplicated people or unique listeners. The script writes directly to both files and does not retain a separate snapshot or last-known-good count.

## Review and Failure Handling

Platform and page-fetch errors are logged to standard error. Several fetch helpers return zero when a request fails, so a partial network/API failure can look like a missing count and remove an existing per-set count on rewrite. Review the Git diff after every run and do not commit an unexpected drop in counts until you have confirmed the API requests succeeded. Run with a clean working tree or save any unrelated edits first, because the output files are overwritten in place.

The displayed total can differ from a platform's own overall audience figure because it sums only links found on the set pages and can include plays from multiple services for the same person.