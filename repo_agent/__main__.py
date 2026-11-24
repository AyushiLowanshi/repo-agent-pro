import argparse
import json
import sys
from pathlib import Path
from .agent import Agent
from .storage import Store

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description='RepoLens: local repository analyst')
    parser.add_argument('--db', default=str(ROOT / 'data' / 'agent.db'), help='SQLite database path')
    sub = parser.add_subparsers(dest='command', required=True)
    ask = sub.add_parser('ask', help='Analyze a repository')
    ask.add_argument('project'); ask.add_argument('question')
    ask.add_argument('--model', default='qwen3:8b'); ask.add_argument('--max-calls', type=int, default=8)
    sub.add_parser('history', help='List recent runs')
    show = sub.add_parser('show', help='Show one saved run'); show.add_argument('run_id', type=int)
    ev = sub.add_parser('eval', help='Run the fixture evaluation')
    ev.add_argument('--model', default='qwen3:8b')
    args = parser.parse_args()
    try:
        store = Store(Path(args.db))
        if args.command == 'ask':
            if args.max_calls < 1 or args.max_calls > 50: raise ValueError('max-calls must be between 1 and 50')
            run_id, answer = Agent(Path(args.project), store, args.model, args.max_calls).run(args.question)
            print(f'\n--- Answer (run {run_id}) ---\n{answer}')
        elif args.command == 'history':
            rows = store.history()
            if not rows: print('No runs yet.')
            for rid, status, model, question, created in rows: print(f'#{rid} [{status}] {model} | {created} | {question}')
        elif args.command == 'show':
            row, events = store.get_run(args.run_id)
            if not row: print('Run not found.'); return 1
            print(json.dumps(dict(zip(['id','project','question','model','status','answer','tool_count','error','started_at','finished_at'], row)), indent=2))
            print('\nTool events:', events)
        else:
            case = json.loads((ROOT / 'evals' / 'cases.json').read_text(encoding='utf-8'))[0]
            run_id, answer = Agent(ROOT / case['project'], store, args.model).run(case['question'])
            checks = {term: term.lower() in answer.lower() for term in case['required_terms']}
            store.evaluation(run_id, case['id'], checks)
            print(f'\n--- Answer ---\n{answer}\n\n--- Heuristic evaluation ---')
            for term, passed in checks.items(): print(f'{"PASS" if passed else "FAIL"}: mentions {term}')
            print(f'Score: {sum(checks.values())}/{len(checks)}. Review correctness manually; keyword checks are not proof.')
            return 0 if all(checks.values()) else 1
    except (Exception, KeyboardInterrupt) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
