# Project Ideas

These are proposed improvements, not implemented features. They focus on repeatable work that is currently spread across separate Markdown pages, metadata files, and manual publishing steps.

## Mixography

**Mixography** is a musical time capsule: a chronological experience that gradually reveals DJ sets from the past, one moment at a time. Each set opens a story from the period when it was recorded: the people, places, events, memories, and circumstances surrounding that mix. The music from the set becomes the soundtrack to its own chapter, connecting the listener to the feeling of that moment.

The experience could unfold as a timeline or a sequence of dated “discoveries,” inviting listeners to travel through the archive at a human pace instead of browsing a catalogue all at once. Each chapter could pair the mix with a personal story, tracklist, photographs or other memorabilia, and links to listen on available platforms. Existing set descriptions and YAML metadata can provide a starting point, while keeping the personal stories curated and authored rather than inventing memories automatically.

## Automation Ideas

1. **Make set metadata the source of truth.** Define a documented YAML schema for every mix and generate the set page, catalogue entry, YouTube description, and tracklist from it. Migrate the existing YAML-backed sets first, then move older pages over gradually to avoid a disruptive all-at-once rewrite.

2. **Add a repository-wide preflight validator.** Check YAML structure, required platform links, unique slugs, valid timestamps, track order and duration, and the existence/readability of audio, cover, font, and track-image files. Emit actionable errors and a machine-readable report so the same checks can run locally and in CI.

3. **Build a one-command media preparation pipeline.** For one set or a batch, run metadata validation and image checks, print the planned FFmpeg commands, render missing or stale videos, and save a per-set result report. Reuse the metadata-driven renderer and make skipped, failed, and completed sets explicit so reruns are safe.

4. **Make play-count refresh resilient and reviewable.** Separate platform API adapters, cache successful responses, add timeouts and consistent retry/backoff, and distinguish a real zero from a failed request. Write both catalogue files atomically, preserve last-known counts on partial failures, and add a dry-run mode before changing tracked Markdown.

5. **Automate quality gates and site deployment with CI.** On pull requests, build each Jekyll site and run the metadata, link, and asset checks; publish the main site and project pages only after those checks pass. Keep external credentials in repository secrets and report which site or set failed, rather than discovering broken pages after publication.
