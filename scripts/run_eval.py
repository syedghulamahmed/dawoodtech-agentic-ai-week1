"""Run 15 live model questions and record actual tools executed."""
import argparse,json
from datetime import datetime
from pathlib import Path
from agentic_assistant.agent import Agent,build_client
from agentic_assistant.cli import configure_logging
from agentic_assistant.config import load_settings
from agentic_assistant.tools import build_registry
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description="Run the 15-question live agent evaluation.")
    parser.add_argument("--limit",type=int,default=15); parser.add_argument("--output",default="tests/results.json"); args=parser.parse_args()
    if not 1<=args.limit<=15: parser.error("--limit must be between 1 and 15.")
    settings=load_settings(); logger=configure_logging(settings.log_path); agent=Agent(build_client(settings),settings,build_registry(settings.sqlite_path),logger)
    cases=json.loads((ROOT/"tests"/"questions.json").read_text(encoding="utf-8"))[:args.limit]; results=[]
    for case in cases:
        print(f"[{case['id']:02d}/15] {case['question']}")
        try:
            summary=agent.run(case["question"]); actual=summary.tools_used; expected=case["expected_tools"]; passed=set(expected).issubset(set(actual))
            results.append({"id":case["id"],"question":case["question"],"expected_tools":expected,"actual_tools":actual,"passed_expected_tool_check":passed,"confidence":summary.confidence,"answer":summary.answer,"error":None})
            print(f"  actual tools: {actual or 'none'} | {'PASS' if passed else 'CHECK'}")
        except Exception as exc:
            results.append({"id":case["id"],"question":case["question"],"expected_tools":case["expected_tools"],"actual_tools":[],"passed_expected_tool_check":False,"confidence":None,"answer":None,"error":f"{type(exc).__name__}: {exc}"})
            print(f"  ERROR: {type(exc).__name__}: {exc}")
    report={"run_type":"live_provider","provider":settings.provider,"model":settings.model,"created_at":datetime.now().astimezone().isoformat(timespec="seconds"),"total":len(results),"passed_expected_tool_check":sum(bool(r["passed_expected_tool_check"]) for r in results),"results":results}
    output=ROOT/args.output; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    md=output.with_suffix(".md"); lines=["# Live 15-question evaluation results","",f"- Provider: `{settings.provider}`",f"- Model: `{settings.model}`",f"- Run time: `{report['created_at']}`",f"- Tool-selection checks: **{report['passed_expected_tool_check']}/{report['total']}**","","| # | Question | Expected tools | Actual tools | Check |","|---:|---|---|---|---|"]
    for row in results:
        q=row["question"].replace("|","\\|"); expected=", ".join(row["expected_tools"]); actual=", ".join(row["actual_tools"]) or "none"; check="PASS" if row["passed_expected_tool_check"] else "CHECK"
        lines.append(f"| {row['id']} | {q} | {expected} | {actual} | {check} |")
    lines += ["","Full answers and errors are stored in the accompanying JSON file.",""]; md.write_text("\n".join(lines),encoding="utf-8")
    print(f"\nSaved: {output.relative_to(ROOT)} and {md.relative_to(ROOT)}")
    return 0 if all(r["passed_expected_tool_check"] for r in results) else 1
if __name__=="__main__": raise SystemExit(main())
