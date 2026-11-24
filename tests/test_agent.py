import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from repo_agent.agent import Agent
from repo_agent.storage import Store

class FakeClient:
    def __init__(self): self.calls = 0
    def chat(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            call = NS(function=NS(name='read_project_file', arguments={'path':'login.py'}))
            return NS(message=NS(tool_calls=[call], content=''))
        return NS(message=NS(tool_calls=[], content='login.py contains a login function.'))

class AgentTest(unittest.TestCase):
    def test_agent_records_run_and_tool(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'project'; root.mkdir()
            (root / 'login.py').write_text('def login(): pass', encoding='utf-8')
            store = Store(Path(d) / 'test.db')
            run_id, answer = Agent(root, store, client=FakeClient(), verbose=False).run('Explain login')
            row, events = store.get_run(run_id)
            self.assertIn('login.py', answer)
            self.assertEqual(row[4], 'completed')
            self.assertEqual(len(events), 1)
