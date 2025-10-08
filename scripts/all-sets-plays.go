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
)

var debug_on = false
var info_on = false
var warn_on = false

// Helper to print debug logs only if debug_on is true
func debugLog(format string, a ...interface{}) {
	if debug_on {
		fmt.Printf(format, a...)
	}
}

func infoLog(format string, a ...interface{}) {
	if info_on {
		fmt.Printf(format, a...)
	}
}

// Helper to print debug logs only if debug_on is true
func warnLog(format string, a ...interface{}) {
	if warn_on {
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
func extractSetLinks(filename string) ([]string, []string, error) {
	debugLog("[DEBUG] Opening file: %s\n", filename)
	file, err := os.Open(filename)
	if err != nil {
		debugLog("[DEBUG] Error opening file %s: %v\n", filename, err)
		return nil, nil, err
	}
	defer file.Close()
	var names []string
	var links []string
	re := regexp.MustCompile(`\* \[(.*?)\]\((.*?)\)`) // Markdown link
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		match := re.FindStringSubmatch(line)
		if len(match) == 3 {
			debugLog("[DEBUG] Found set: %s (%s)\n", match[1], match[2])
			names = append(names, match[1])
			links = append(links, match[2])
		}
	}
	debugLog("[DEBUG] Extracted %d sets\n", len(names))
	return names, links, nil
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
	clientID := os.Getenv("SOUNDCLOUD_CLIENT_ID")
	if clientID == "" {
		warnLog("[WARN] SoundCloud client ID not set in environment. Skipping.\n")
		return 0
	}
	// Step 1: Resolve the track to get the API resource
	resolveAPI := fmt.Sprintf("https://api.soundcloud.com/resolve?url=%s&client_id=%s", url.QueryEscape(scURL), clientID)
	debugLog("[DEBUG] Resolving SoundCloud URL: %s\n", resolveAPI)
	resp, err := http.Get(resolveAPI)
	if err != nil {
		debugLog("[DEBUG] Error resolving SoundCloud URL: %v\n", err)
		return 0
	}
	defer resp.Body.Close()
	if resp.StatusCode != 302 && resp.StatusCode != 200 {
		debugLog("[DEBUG] SoundCloud resolve returned status: %d\n", resp.StatusCode)
		return 0
	}
	var trackData struct {
		ID            int `json:"id"`
		PlaybackCount int `json:"playback_count"`
	}
	// If 302, follow redirect to get track info
	if resp.StatusCode == 302 {
		location := resp.Header.Get("Location")
		debugLog("[DEBUG] Redirected to: %s\n", location)
		resp2, err := http.Get(location + "?client_id=" + clientID)
		if err != nil {
			debugLog("[DEBUG] Error fetching redirected SoundCloud track: %v\n", err)
			return 0
		}
		defer resp2.Body.Close()
		if err := json.NewDecoder(resp2.Body).Decode(&trackData); err != nil {
			debugLog("[DEBUG] Error decoding SoundCloud track response: %v\n", err)
			return 0
		}
	} else {
		if err := json.NewDecoder(resp.Body).Decode(&trackData); err != nil {
			debugLog("[DEBUG] Error decoding SoundCloud resolve response: %v\n", err)
			return 0
		}
	}
	debugLog("[DEBUG] SoundCloud playback_count: %d\n", trackData.PlaybackCount)
	return trackData.PlaybackCount
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
	re1 := regexp.MustCompile(`youtube\.com/watch\?v=([a-zA-Z0-9_-]+)`)
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
	infoLog("[INFO] External links found - Mixcloud: %s, SoundCloud: %s, YouTube: %s\n", mixcloud, soundcloud, youtube)
	return
}

func main() {
	debugLog("[DEBUG] Starting all-sets-plays.go")
	setNames, setLinks, err := extractSetLinks("../all-sets.md")
	if err != nil {
		fmt.Println("Error reading all-sets.md:", err)
		return
	}
	debugLog("[DEBUG] Processing %d sets\n", len(setLinks))
	for i, link := range setLinks {
		// debugLog("[DEBUG] Processing set %d: %s (%s)\n", i+1, setNames[i], link)
		page, err := fetchURL(link)
		if err != nil {
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
		// Output in requested markdown style, only add plays info if plays > 0
		if plays > 0 {
			fmt.Printf("* [%s](%s) _//_ %d🎶\n", setNames[i], link, plays)
		} else {
			fmt.Printf("* [%s](%s)\n", setNames[i], link)
		}
	}
}
