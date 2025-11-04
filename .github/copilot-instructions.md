## Purpose
Be immediately productive editing this repository: it's a multi-folder Jekyll-based static site containing DJ set pages, track lists and small sub-sites (e.g. `progressive-awake`, `fresh-dance-music`, `quantum-energy`). Use these notes to follow repo conventions and avoid breaking links, image paths, or site config.

## Project snapshot (what to know)
- This repo uses Jekyll-style config files (`_config.yml`) and the `jekyll-theme-slate` theme (see `/_config.yml`). Multiple folders (e.g. `progressive-awake`, `fresh-dance-music`, `music`, `quantum-energy`) contain their own content and often their own `_config.yml`.
- Content files are plain Markdown under each section (e.g. `progressive-awake/first-snow-november-2010.md`). Many pages use inline metadata lines like `Date: 2010-11-10` and `Tags: ...` instead of YAML front-matter — keep existing style when editing unless you intentionally convert the file.
- Images and local assets use relative paths (e.g. `./images/foo.jpg`, `./shivioua-background.png`). Preserve relative links when moving or renaming files.
- External integrations: SoundCloud / Mixcloud / YouTube links and OneDrive MP3 download links are embedded directly in pages. Changing those links affects published content.

## When editing content
- Edit the Markdown file in the section folder (e.g. to update a set, edit `fresh-dance-music/primrose-april-2008.md`). Keep the surrounding README in that folder in sync (each section contains a `README.md` listing the pages).
- Preserve small inline metadata blocks (Date/Tags) unless converting to YAML front-matter — inconsistent metadata styles exist across files.
- Keep image and download links relative. If you rename/move an image, update every page referring to `./images/...` or `../img/...` as appropriate.

## Build & preview (local)
- The site is configured for Jekyll (see `/_config.yml`). To preview locally (requires Ruby & Jekyll):
  - Install Ruby and Bundler, then run `bundle install` (if there's a Gemfile) or install `jekyll`.
  - From the repo root run: `bundle exec jekyll serve` or `jekyll serve` to preview on localhost.
- Quick check: open the top-level `README.md` and a section README (e.g. `fresh-dance-music/README.md`) to confirm internal links render as expected.

## Code patterns & conventions
- Directory-per-section: each top-level folder groups related sets/tracks (e.g. `progressive-awake/*`). Treat each folder as a small sub-site when editing.
- Anti-patterns to avoid: converting only some files to YAML front-matter; breaking relative paths; changing base URL assumptions without updating `_config.yml`.

## Useful files to inspect when making changes
- `/_config.yml` (root) — site theme and global config (google analytics, show_downloads, etc.)
- `progressive-awake/`, `fresh-dance-music/`, `quantum-energy/`, `music/` — main content directories
- `*_README.md` inside each folder — lists pages and is the user-facing index for that section
- `all-sets-sorted.md` — aggregated, cross-section list used for play-count ordering and publishing status markers

## All sets and all sets sorted

- `all-sets.md` contains the full list of sets with links and play counts. When adding a new set, update this file to include it.
- `all-sets-sorted.md` is used to maintain a sorted list of sets by play counts and to indicate publishing status. When adding a new set, if it is published, add it to this file without the `NOT PUBLISHED YET` marker.
- both files content play count is added using all-sets-plays.go script

## Examples (do this)
- To add a new set called “Rebalancing (December 2022)”:
  1. Add `fresh-dance-music/rebalancing-december-2022.md` following the style of nearby `.md` posts.
  2. Update `fresh-dance-music/README.md` to include the new link.
  3. If this is a published set add it to `all-sets-sorted.md` (remove the `NOT PUBLISHED YET` marker).

## Example Usage

This is how you can use the canonical template:

```markdown
---
layout: post
title: "My First Post"
date: 2025-11-04 12:00:00
categories: [example]
tags: [first, post]
---

# My First Post

This is the content of my first post.

## Additional Sections

- Introduction
- Conclusion
```

## Commit / PR notes for AI edits
- Make minimal, focused edits in a single PR. When modifying paths or metadata, include a short PR description listing files changed and why.
- Preserve link targets and external download URLs unless given explicit instructions to change them.

## If you need to refactor metadata
- If you decide to normalize metadata to YAML front-matter, convert entire folders in one change and update references in `README.md` files to avoid mixed formats.

If anything above is unclear or you want me to include additional examples (e.g. a template `.md` snippet matching repository style), tell me which folder/page to model and I will update this guidance.
