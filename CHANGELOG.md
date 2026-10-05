# Changelog

This file summarizes the main milestones across the Shivioua repositories. It is an aggregate project history, not a release-by-release list of every copy edit, link fix, or generated play-count refresh. The review covers 403 commits across the five repositories through 2026-10-05.

## 2026

### October

- Updated set descriptions in Progressive Awake and Quantum Energy. The main site's latest play-count refresh reported approximately 6.1 thousands plays in total.

### July

- Expanded the DJ-set video generator with per-track image scenes, animated zoom and pan profiles for the different mix brands, cross-dissolve transitions, and improved duration handling. Added an image inspection report to flag missing or low-resolution artwork before rendering.
- Added structured YAML metadata for the Progressive Awake mixes “7 months of dream” and “Opium”, including descriptions, timestamped tracklists, and per-track artwork paths. Refined their descriptions and track data afterward.
- Extended the play-count updater to fetch Mixcloud, SoundCloud, and YouTube counts, and to regenerate the most-listened-first set catalogue in the same run.
- Added further techniques to the Brazilian jiu-jitsu library, bringing its numbered entries through 196. The new Technique of the Day page can select a technique by ID or at random; its catalogue also gained YouTube imports, counts, update dates, and support for videos that should not be embedded.

### April-June

- Added the Shivioua.Rent information page and improved its rental price table and presentation.
- Added a Brazilian jiu-jitsu technique catalogue and a no-gi Technique of the Day page, then refined navigation, loading feedback, video handling, and the technique data format.
- Added an AI dashboard page. The history records this as an initial dashboard addition; it does not establish a completed AI workflow.

### February-March

- Continued normalizing set descriptions and metadata across Progressive Awake, Fresh Dance Music, and Quantum Energy.

## 2025

- Published “Freedom (October 2025)” in Fresh Dance Music, with its track listing and tags.
- Published “Rolls & Bass (December 2025)” in Quantum Energy and subsequently added its platform links and descriptive details.
- Improved the play-count tooling: added SoundCloud support, ranked sets by plays, counted sets including live YouTube sessions, and refined the generated totals and formatting.
- Corrected archive metadata, artwork and download links across older DJ sets, and migrated several MP3 download links to OneDrive or Patreon.

## 2024

- Added the Progressive Awake set “Backstreet Bar (August 2024)” and updated its catalogue presentation.
- Continued restoring and improving older Progressive Awake entries with corrected artwork, links, track information, and platform playlists.
- Updated Fresh Dance Music branding and platform links as sets were consolidated under the Shivioua profile; removed outdated social links and retired content.

## 2023

- Established the main Shivioua Jekyll site and moved the Progressive Awake, Fresh Dance Music, and Quantum Energy set archives under the Shivioua web presence. Added GA4 tracking and consolidated social, listening, and support links.
- Added an all-DJ-sets archive and an all-tracks page to the main site.
- Created dedicated repositories for the Progressive Awake, Fresh Dance Music, Quantum Energy, and Music pages. The Music archive covers tracks, remixes, and live-coding sessions.
- Updated archive pages with listening links, playlists, corrected downloads, and Patreon support information.

## Project Status

- The public presence is a collection of static Jekyll sites and Markdown-based music archives.
- Repeated maintenance has begun to move into Python tooling: play-count refresh and sorting, image checks, and metadata-driven video rendering. The renderer prepares video files but does not upload or schedule them on YouTube.
- The main site has also grown beyond the music archives to include BJJ reference pages, the rental information page, and an initial AI dashboard page.
- Set descriptions, metadata, links, and image assets are still maintained across many individual files. The project ideas list records possible next steps for consolidating and validating those workflows.