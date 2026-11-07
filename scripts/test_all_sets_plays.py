import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import all_sets_plays as plays


class AllSetsPlaysTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name).resolve()
        self.catalogue = self.root / "shivioua.github.io" / "all-sets.md"
        self.catalogue.parent.mkdir()
        self.sorted_catalogue = self.catalogue.with_name("all-sets-sorted.md")
        for name, value in (
            ("REPOSITORIES_DIR", self.root),
            ("ALL_SETS_MD", str(self.catalogue)),
            ("ALL_SETS_SORTED_MD", str(self.sorted_catalogue)),
            ("debug_on", False),
        ):
            patcher = patch.object(plays, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        network = patch.object(
            plays.urllib.request, "urlopen",
            side_effect=AssertionError("Unexpected network request"),
        )
        network.start()
        self.addCleanup(network.stop)
        self.url = "https://shivioua.github.io/progressive-awake/moon-trip-b2b-august-2026.html"

    def write_set(self, content):
        filename = self.root / "progressive-awake" / "moon-trip-b2b-august-2026.md"
        filename.parent.mkdir(exist_ok=True)
        filename.write_text(content, encoding="utf-8")

    def test_read_unpublished_set_locally(self):
        self.write_set("# Moon Trip B2B\n")
        self.assertEqual(plays.read_set_page(self.url + "?test=1#listen"), "# Moon Trip B2B\n")

    def test_external_links_in_markdown_and_html(self):
        urls = (
            "https://www.mixcloud.com/shivioua/moon-trip/",
            "https://soundcloud.com/shivioua/moon-trip?secret_token=test",
            "https://www.youtube.com/watch?v=test123&feature=share",
        )
        for template in ('[Listen]({})\n', '<a href="{}">Listen</a>\n'):
            with self.subTest(template=template):
                page = "".join(template.format(url) for url in urls)
                self.assertEqual(plays.find_external_links(page), urls)
        self.assertEqual(
            plays.find_external_links("[YouTube](https://youtu.be/test123)\n")[2],
            "https://youtu.be/test123",
        )

    def test_update_counts_totals_and_sorted_catalogue(self):
        self.write_set(
            "[Mixcloud](https://www.mixcloud.com/shivioua/moon-trip/)\n"
            "[SoundCloud](https://soundcloud.com/shivioua/moon-trip)\n"
            "[YouTube](https://youtu.be/test123)\n"
        )
        self.catalogue.write_text(
            f"* [**Moon Trip B2B (August 2026)**]({self.url}) _//_ 21\U0001f3a7\n"
            "\nTotal plays: **21\U0001f3a7**  \nTotal amount of sets: **1\U0001f3b6**  \n",
            encoding="utf-8",
        )
        with (
            patch.object(plays, "get_mixcloud_plays", return_value=22) as mixcloud,
            patch.object(plays, "get_soundcloud_plays", return_value=3) as soundcloud,
            patch.object(plays, "get_youtube_plays", return_value=5) as youtube,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            plays.main()
        mixcloud.assert_called_once_with("https://www.mixcloud.com/shivioua/moon-trip/")
        soundcloud.assert_called_once_with("https://soundcloud.com/shivioua/moon-trip")
        youtube.assert_called_once_with("https://youtu.be/test123")
        for filename in (self.catalogue, self.sorted_catalogue):
            content = filename.read_text(encoding="utf-8")
            self.assertIn(f"]({self.url}) _//_ 30\U0001f3a7", content)
            self.assertIn("Total plays: **30\U0001f3a7**", content)
            self.assertIn("Total amount of sets: **1\U0001f3b6**", content)

    def test_missing_local_file_logs_error_without_writing_catalogues(self):
        original = f"* [Moon Trip]({self.url}) _//_ 21\U0001f3a7\n"
        self.catalogue.write_text(original, encoding="utf-8")
        self.sorted_catalogue.write_text("Existing sorted catalogue\n", encoding="utf-8")
        errors = io.StringIO()
        with (
            patch.object(plays, "debug_on", True),
            contextlib.redirect_stderr(errors),
            self.assertRaises(FileNotFoundError),
        ):
            plays.main()
        self.assertIn("[ERROR] Cannot read local set file", errors.getvalue())
        self.assertEqual(self.catalogue.read_text(encoding="utf-8"), original)
        self.assertEqual(
            self.sorted_catalogue.read_text(encoding="utf-8"), "Existing sorted catalogue\n",
        )

    def test_reject_unsupported_or_outside_repository_urls(self):
        for url in (
            "https://example.com/progressive-awake/set.html",
            "https://shivioua.github.io/progressive-awake/set.txt",
            "https://shivioua.github.io/%2e%2e/outside.html",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                plays.read_set_page(url)


if __name__ == "__main__":
    unittest.main()
