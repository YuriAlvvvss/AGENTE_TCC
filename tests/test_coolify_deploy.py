import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CoolifyDeployTests(unittest.TestCase):
    def test_web_image_packages_stylesheet_directory(self):
        dockerfile = (ROOT / "web" / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("COPY styles /usr/share/nginx/html/styles", dockerfile)

    def test_login_visibility_has_inline_hidden_fallback(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn(".hidden { display: none !important; }", html)


if __name__ == "__main__":
    unittest.main()
