import tempfile
import unittest
from pathlib import Path
from repo_agent.tools import RepositoryTools

class TestTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        (self.root / 'login.py').write_text('def login():\n    return True\n', encoding='utf-8')
        (self.root / '.env').write_text('SECRET=hidden', encoding='utf-8')
        self.tools = RepositoryTools(self.root)
    def tearDown(self): self.temp.cleanup()
    def test_search(self): self.assertIn('login.py:1', self.tools.search_files('login'))
    def test_read(self): self.assertIn('def login', self.tools.read_file('login.py'))
    def test_traversal_blocked(self): self.assertIn('Error:', self.tools.read_file('../outside.txt'))
    def test_sensitive_blocked(self): self.assertIn('Error:', self.tools.read_file('.env'))
    def test_absolute_path_blocked(self): self.assertIn('Error:', self.tools.read_file(str(self.root / 'login.py')))
    def test_excluded_not_listed(self): self.assertNotIn('.env', self.tools.list_files())
