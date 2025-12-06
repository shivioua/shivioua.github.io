// all-sets-plays.go
// Script to parse all-sets.md, extract set links, and sum up plays from Mixcloud, SoundCloud, and YouTube.
// Note: For SoundCloud and YouTube, API keys may be required for full functionality.
// This script uses basic HTTP requests and HTML parsing for demonstration.

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

var debug_on = false

// Helper to print debug logs only if debug_on is true
func debugLog(format string, a ...interface{}) {
	if debug_on {
		fmt.Printf(format, a...)
	}
}

// Helper to fetch page content
func fetchURL(url string) (string, error) {
	debugLog("[DEBUG] Fetching URL: %s\n", url)
	resp, err := http.Get(url)
	if err != nil {
		debugLog("[DEBUG] Error fetching URL %s: %v\n", url, err)
		return "", err
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		debugLog("[DEBUG] Error reading body for URL %s: %v\n", url, err)
		return "", err
	}
	debugLog("[DEBUG] Fetched %d bytes from %s\n", len(body), url)
	return string(body), nil
}

// Extract set links from all-sets.md
// Now returns names, links (may be empty for unpublished/non-linked items), rawLines (original trimmed list line), error
func extractSetLinks(filename string) ([]string, []string, []string, error) {
	debugLog("[DEBUG] Opening file: %s\n", filename)
	file, err := os.Open(filename)
	if err != nil {
		debugLog("[DEBUG] Error opening file %s: %v\n", filename, err)
		return nil, nil, nil, err
	}
	defer file.Close()
	var names []string
	var links []string
	var rawLines []string
	re := regexp.MustCompile(`\* \[(.*?)\]\((.*?)\)`) // Markdown link
	scanner := bufio.NewScanner(file)
	seen := make(map[string]bool)
	for scanner.Scan() {
		line := scanner.Text()
		trim := strings.TrimSpace(line)
		// Only care about list items that start with "* "
		if !strings.HasPrefix(trim, "* ") {
			continue
		}
		// Try to find a markdown link
		match := re.FindStringSubmatch(trim)
		if len(match) == 3 {
			link := match[2]
			name := match[1]
			key := link
			if key == "" {
				key = trim
			}
			if seen[key] {
				continue
			}
			seen[key] = true
			debugLog("[DEBUG] Found set (linked): %s (%s)\n", name, link)
			names = append(names, name)
			links = append(links, link)
			rawLines = append(rawLines, trim)
		} else {
			// Non-linked list item (e.g. "Faixa Azul (June 2023) _// NOT PUBLISHED YET_")
			key := trim
			if seen[key] {
				continue
			}
			seen[key] = true
			// Use the whole trimmed line as the "name" placeholder (caller will print rawLines)
			debugLog("[DEBUG] Found set (unlinked/raw): %s\n", trim)
			names = append(names, trim) // name placeholder
			links = append(links, "")   // empty link
			rawLines = append(rawLines, trim)
		}
	}
	debugLog("[DEBUG] Extracted %d unique sets (including unlinked)\n", len(names))
	return names, links, rawLines, nil
}

// Dummy functions for play count extraction (to be implemented for each platform)
func getMixcloudPlays(mixcloudURL string) int {
	debugLog("[DEBUG] getMixcloudPlays called with URL: %s\n", mixcloudURL)
	// Extract username and slug from the Mixcloud URL
	re := regexp.MustCompile(`https://www\.mixcloud\.com/([^/]+)/([^/?#]+)/?`)
	matches := re.FindStringSubmatch(mixcloudURL)
	if len(matches) < 3 {
		debugLog("[DEBUG] Could not parse Mixcloud URL: %s\n", mixcloudURL)
		return 0
	}
	username := matches[1]
	slug := matches[2]
	apiURL := fmt.Sprintf("https://api.mixcloud.com/%s/%s/", url.PathEscape(username), url.PathEscape(slug))
	debugLog("[DEBUG] Fetching Mixcloud API URL: %s\n", apiURL)
	resp, err := http.Get(apiURL)
	if err != nil {
		debugLog("[DEBUG] Error fetching Mixcloud API: %v\n", err)
		return 0
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		debugLog("[DEBUG] Mixcloud API returned status: %d\n", resp.StatusCode)
		return 0
	}
	var data struct {
		PlayCount int `json:"play_count"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		debugLog("[DEBUG] Error decoding Mixcloud API response: %v\n", err)
		return 0
	}
	debugLog("[DEBUG] Mixcloud play_count: %d\n", data.PlayCount)
	return data.PlayCount
}
func getSoundcloudPlays(scURL string) int {
	debugLog("[DEBUG] getSoundcloudPlays called with URL: %s\n", scURL)

	// 1) Prefer explicit OAuth token in env
	oauthToken := os.Getenv("SOUNDCLOUD_OAUTH_TOKEN")
	if oauthToken != "" {
		debugLog("[DEBUG] Using SOUNDCLOUD_OAUTH_TOKEN\n")
		if plays, ok := resolveSoundCloudWithToken(scURL, oauthToken); ok {
			return plays
		}
		debugLog("[WARN] SoundCloud OAuth token request failed, will try other methods\n")
	}

	// 2) Try to obtain a token from client_id + client_secret (if provided)
	clientID := os.Getenv("SOUNDCLOUD_CLIENT_ID")
	clientSecret := os.Getenv("SOUNDCLOUD_CLIENT_SECRET")
	if clientID != "" && clientSecret != "" {
		debugLog("[DEBUG] Attempting OAuth token exchange with client_id+client_secret\n")
		tokenURL := "https://api.soundcloud.com/oauth2/token"
		form := url.Values{
			"client_id":     {clientID},
			"client_secret": {clientSecret},
			"grant_type":    {"client_credentials"},
		}
		resp, err := http.PostForm(tokenURL, form)
		if err != nil {
			debugLog("[ERROR] Error requesting SoundCloud token: %v\n", err)
		} else {
			defer resp.Body.Close()
			if resp.StatusCode == 200 {
				var tok struct {
					AccessToken string `json:"access_token"`
				}
				if err := json.NewDecoder(resp.Body).Decode(&tok); err == nil && tok.AccessToken != "" {
					debugLog("[DEBUG] Obtained SoundCloud OAuth token via client credentials\n")
					if plays, ok := resolveSoundCloudWithToken(scURL, tok.AccessToken); ok {
						return plays
					}
					debugLog("[WARN] SoundCloud resolve with obtained token failed, will try client_id resolve or HTML fallback\n")
				} else {
					debugLog("[DEBUG] Token exchange decode error or empty token: %v\n", err)
				}
			} else {
				debugLog("[DEBUG] Token endpoint returned status: %d\n", resp.StatusCode)
			}
		}
	} else {
		debugLog("[ERROR] SOUNDCLOUD_CLIENT_ID or SOUNDCLOUD_CLIENT_SECRET not set, skipping token exchange\n")
	}

	// 3) If client_id available, try legacy resolve?client_id=... (may return 401)
	if clientID != "" {
		resolveAPI := fmt.Sprintf("https://api.soundcloud.com/resolve?url=%s&client_id=%s", url.QueryEscape(scURL), clientID)
		debugLog("[DEBUG] Resolving SoundCloud URL (client_id): %s\n", resolveAPI)
		resp, err := http.Get(resolveAPI)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == 200 {
				var trackData struct {
					ID            int `json:"id"`
					PlaybackCount int `json:"playback_count"`
				}
				if err := json.NewDecoder(resp.Body).Decode(&trackData); err == nil {
					debugLog("[DEBUG] SoundCloud playback_count (API client_id): %d\n", trackData.PlaybackCount)
					return trackData.PlaybackCount
				}
			}
			if resp.StatusCode == 302 {
				location := resp.Header.Get("Location")
				debugLog("[DEBUG] Redirected to: %s\n", location)
				resp2, err := http.Get(location + "?client_id=" + clientID)
				if err == nil {
					defer resp2.Body.Close()
					var trackData struct {
						ID            int `json:"id"`
						PlaybackCount int `json:"playback_count"`
					}
					if err := json.NewDecoder(resp2.Body).Decode(&trackData); err == nil {
						debugLog("[DEBUG] SoundCloud playback_count (API redirect): %d\n", trackData.PlaybackCount)
						return trackData.PlaybackCount
					}
				}
			}
			if resp.StatusCode == 401 {
				debugLog("[WARN] SoundCloud resolve returned 401 (invalid client_id). Will fall back to HTML parsing\n")
			} else {
				debugLog("[DEBUG] SoundCloud resolve returned status: %d\n", resp.StatusCode)
			}
		} else {
			debugLog("[DEBUG] Error resolving SoundCloud URL with client_id: %v\n", err)
		}
	}

	// 4) HTML fallback: fetch the SoundCloud page and try to extract playback_count from embedded JSON
	debugLog("[DEBUG] Fetching SoundCloud page for HTML fallback: %s\n", scURL)
	respPage, err := http.Get(scURL)
	if err != nil {
		debugLog("[DEBUG] Error fetching SoundCloud page: %v\n", err)
		return 0
	}
	defer respPage.Body.Close()
	body, err := ioutil.ReadAll(respPage.Body)
	if err != nil {
		debugLog("[DEBUG] Error reading SoundCloud page body: %v\n", err)
		return 0
	}
	re := regexp.MustCompile(`"playback_count"\s*:\s*([0-9]+)`)
	if m := re.FindSubmatch(body); len(m) == 2 {
		if v, err := strconv.Atoi(string(m[1])); err == nil {
			debugLog("[DEBUG] SoundCloud playback_count (HTML fallback): %d\n", v)
			return v
		}
	}
	re2 := regexp.MustCompile(`playback_count\s*:\s*([0-9]+)`)
	if m := re2.FindSubmatch(body); len(m) == 2 {
		if v, err := strconv.Atoi(string(m[1])); err == nil {
			debugLog("[DEBUG] SoundCloud playback_count (HTML fallback alt): %d\n", v)
			return v
		}
	}
	debugLog("[WARN] Could not determine SoundCloud playback_count for %s\n", scURL)
	return 0
}

// Helper to resolve a SoundCloud URL using an OAuth token. Returns (plays, ok)
func resolveSoundCloudWithToken(scURL, token string) (int, bool) {
	resolveAPI := fmt.Sprintf("https://api.soundcloud.com/resolve?url=%s", url.QueryEscape(scURL))
	req, err := http.NewRequest("GET", resolveAPI, nil)
	if err != nil {
		debugLog("[DEBUG] NewRequest error: %v\n", err)
		return 0, false
	}
	req.Header.Set("Authorization", "OAuth "+token)
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		debugLog("[DEBUG] Error resolving SoundCloud URL with token: %v\n", err)
		return 0, false
	}
	defer resp.Body.Close()
	if resp.StatusCode == 200 {
		var trackData struct {
			ID            int `json:"id"`
			PlaybackCount int `json:"playback_count"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&trackData); err == nil {
			debugLog("[DEBUG] SoundCloud playback_count (API OAuth): %d\n", trackData.PlaybackCount)
			return trackData.PlaybackCount, true
		}
		return 0, false
	}
	// handle redirect
	if resp.StatusCode == 302 {
		location := resp.Header.Get("Location")
		debugLog("[DEBUG] Token-resolve redirected to: %s\n", location)
		req2, _ := http.NewRequest("GET", location, nil)
		req2.Header.Set("Authorization", "OAuth "+token)
		resp2, err := client.Do(req2)
		if err != nil {
			debugLog("[DEBUG] Error fetching redirected SoundCloud track with token: %v\n", err)
			return 0, false
		}
		defer resp2.Body.Close()
		if resp2.StatusCode == 200 {
			var trackData struct {
				ID            int `json:"id"`
				PlaybackCount int `json:"playback_count"`
			}
			if err := json.NewDecoder(resp2.Body).Decode(&trackData); err == nil {
				debugLog("[DEBUG] SoundCloud playback_count (API OAuth redirect): %d\n", trackData.PlaybackCount)
				return trackData.PlaybackCount, true
			}
		}
	}
	debugLog("[DEBUG] SoundCloud resolve with token returned status: %d\n", resp.StatusCode)
	return 0, false
}

func getYouTubePlays(ytURL string) int {
	debugLog("[DEBUG] getYouTubePlays called with URL: %s\n", ytURL)
	apiKey := os.Getenv("YOUTUBE_API_KEY")
	if apiKey == "" {
		debugLog("[WARN] YouTube API key not set in environment. Skipping.\n")
		return 0
	}
	// Extract video ID from URL
	var videoID string
	// Handle https://www.youtube.com/watch?v=VIDEO_ID or https://www.youtube.com/live/VIDEO_ID
	re1 := regexp.MustCompile(`youtube\.com/(?:watch\?v=|live/)([a-zA-Z0-9_-]+)`)
	// Handle https://youtu.be/VIDEO_ID
	re2 := regexp.MustCompile(`youtu\.be/([a-zA-Z0-9_-]+)`)

	if m := re1.FindStringSubmatch(ytURL); len(m) == 2 {
		videoID = m[1]
	} else if m := re2.FindStringSubmatch(ytURL); len(m) == 2 {
		videoID = m[1]
	} else {
		debugLog("[DEBUG] Could not extract YouTube video ID from URL: %s\n", ytURL)
		return 0
	}
	apiURL := fmt.Sprintf(
		"https://www.googleapis.com/youtube/v3/videos?part=statistics&id=%s&key=%s",
		videoID, apiKey,
	)
	debugLog("[DEBUG] Fetching YouTube API URL: %s\n", apiURL)
	resp, err := http.Get(apiURL)
	if err != nil {
		debugLog("[DEBUG] Error fetching YouTube API: %v\n", err)
		return 0
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		debugLog("[DEBUG] YouTube API returned status: %d\n", resp.StatusCode)
		return 0
	}
	var data struct {
		Items []struct {
			Statistics struct {
				ViewCount string `json:"viewCount"`
			} `json:"statistics"`
		} `json:"items"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		debugLog("[DEBUG] Error decoding YouTube API response: %v\n", err)
		return 0
	}
	if len(data.Items) == 0 {
		debugLog("[DEBUG] No items found for video ID: %s\n", videoID)
		return 0
	}
	viewCountStr := data.Items[0].Statistics.ViewCount
	var viewCount int
	if _, err := fmt.Sscanf(viewCountStr, "%d", &viewCount); err != nil {
		debugLog("[DEBUG] Error parsing viewCount: %v\n", err)
		return 0
	}
	debugLog("[DEBUG] YouTube viewCount: %d\n", viewCount)
	return viewCount
}

// Find external links in set page (Mixcloud, SoundCloud, YouTube)
func findExternalLinks(page string) (mixcloud, soundcloud, youtube string) {
	// debugLog("[DEBUG] Finding external links in page\n")
	// debugLog("[DEBUG] Page content: %s...\n", page) // Print first 100 chars for debugging")
	mixcloudRe := regexp.MustCompile(`https://www.mixcloud.com/[^"]+`)
	debugLog("[DEBUG] mixcloudRe: %v\n", mixcloudRe)
	soundcloudRe := regexp.MustCompile(`https://soundcloud.com/[^"]+`)
	youtubeRe := regexp.MustCompile(`https://(www\.)?youtube.com/[^"]+|https://youtu.be/[^"]+`)
	if m := mixcloudRe.FindString(page); m != "" {
		debugLog("[DEBUG] Found Mixcloud link: %s\n", m)
		mixcloud = m
	}
	if s := soundcloudRe.FindString(page); s != "" {
		soundcloud = s
	}
	if y := youtubeRe.FindString(page); y != "" {
		youtube = y
	}
	debugLog("[DEBUG] External links found - Mixcloud: %s, SoundCloud: %s, YouTube: %s\n", mixcloud, soundcloud, youtube)
	return
}

// Format play count with "k" for thousands, "M" for millions, etc.
func formatPlays(n int) string {
	switch {
	case n >= 1_000_000:
		return fmt.Sprintf("%.1fM", float64(n)/1_000_000)
	case n >= 1_000:
		return fmt.Sprintf("%.1fk", float64(n)/1_000)
	default:
		return fmt.Sprintf("%d", n)
	}
}

// printSortedSets reads all-sets.md, collects lines that start with "* ", extracts play counts (digits before 🎶 if present),
// deduplicates entries by link, sorts entries by plays descending and prints them to stdout.
func printSortedSets(path string) error {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(string(data), "\n")
	type entry struct {
		line  string
		plays int
		link  string
	}
	var entries []entry
	rePlays := regexp.MustCompile(`([0-9]+)🎧`)
	// link extraction from markdown link
	reLink := regexp.MustCompile(`\((https?://[^\s)]+)\)`)
	seenLinks := make(map[string]bool)
	for _, ln := range lines {
		trim := strings.TrimSpace(ln)
		if !strings.HasPrefix(trim, "* ") {
			continue
		}
		// extract URL to dedupe
		link := ""
		if m := reLink.FindStringSubmatch(trim); len(m) == 2 {
			link = m[1]
		}
		if link != "" && seenLinks[link] {
			continue // skip duplicate list line for same link
		}
		plays := 0
		if m := rePlays.FindStringSubmatch(trim); len(m) == 2 {
			if v, err := strconv.Atoi(m[1]); err == nil {
				plays = v
			}
		}
		entries = append(entries, entry{line: trim, plays: plays, link: link})
		if link != "" {
			seenLinks[link] = true
		}
	}
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].plays > entries[j].plays
	})
	for _, e := range entries {
		fmt.Println(e.line)
	}
	return nil
}

func main() {
	// if invoked as: go run all-sets-plays.go sort
	if len(os.Args) > 1 && os.Args[1] == "sort" {
		if err := printSortedSets("../all-sets.md"); err != nil {
			fmt.Println("Error:", err)
			os.Exit(1)
		}
		return
	}

	debugLog("[DEBUG] Starting all-sets-plays.go")
	setNames, setLinks, rawLines, err := extractSetLinks("../all-sets.md")
	if err != nil {
		fmt.Println("Error reading all-sets.md:", err)
		return
	}
	debugLog("[DEBUG] Processing %d unique sets\n", len(setLinks))
	totalPlays := 0
	totalSets := 0
	processed := make(map[string]bool)
	for i, link := range setLinks {
		// build dedupe key: prefer link when present, otherwise use raw line
		key := link
		if key == "" {
			key = rawLines[i]
		}
		if processed[key] {
			continue // skip if already processed
		}
		processed[key] = true
		totalSets++

		// If there's no external link (unpublished / raw item), print the original line unchanged
		if link == "" {
			fmt.Println(rawLines[i])
			continue
		}

		page, err := fetchURL(link)
		if err != nil {
			// still print the linked item without plays if fetch failed
			fmt.Printf("* [%s](%s)\n", setNames[i], link)
			continue
		}
		mixcloud, soundcloud, youtube := findExternalLinks(page)
		plays := 0
		if mixcloud != "" {
			plays += getMixcloudPlays(mixcloud)
		}
		if soundcloud != "" {
			plays += getSoundcloudPlays(soundcloud)
		}
		if youtube != "" {
			plays += getYouTubePlays(youtube)
		}
		totalPlays += plays
		// Output in requested markdown style, only add plays info if plays > 0
		if plays > 0 {
			fmt.Printf("* [%s](%s) _//_ %d🎧\n", setNames[i], link, plays)
		} else {
			fmt.Printf("* [%s](%s)\n", setNames[i], link)
		}
	}
	fmt.Printf("\nTotal plays: **%s🎧**\n", formatPlays(totalPlays))
	fmt.Printf("Total amount of sets: **%d🎶**\n", totalSets)
}
