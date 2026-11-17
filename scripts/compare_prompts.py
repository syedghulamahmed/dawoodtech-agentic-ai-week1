"""Compare three system prompts using the configured live provider."""
from datetime import datetime
from pathlib import Path
from agentic_assistant.agent import build_client
from agentic_assistant.config import load_settings
ROOT=Path(__file__).resolve().parents[1]
REQUEST="Explain BFS and DFS to a beginner, then give one practical use case for each."
PROMPTS={
"A — Basic":"You are a helpful assistant. Answer the user's question clearly.",
"B — Role + constraints":"You are a patient computer science tutor. Explain concepts for a first-year student. Use simple language, one concise definition per concept, and one practical use case each. Do not add unrelated details.",
"C — Role + structure + example":"You are an exam-focused computer science tutor. Explain BFS and DFS in simple language. For each: give the core idea, a small real-world analogy, and one practical use case. Finish with a compact comparison table. Example style: 'BFS checks nearby nodes before moving deeper.' Be accurate and avoid unsupported claims."
}
def main():
    settings=load_settings(); client=build_client(settings); rows=[]
    for label,prompt in PROMPTS.items():
        response=client.chat.completions.create(model=settings.model,temperature=settings.temperature,max_tokens=settings.max_tokens,messages=[{"role":"system","content":prompt},{"role":"user","content":REQUEST}])
        answer=response.choices[0].message.content or "[No text content returned]"; rows.append((label,prompt,answer)); print(f"\n{label}\n{answer}\n")
    output=["# System prompt comparison","",f"- Provider: `{settings.provider}`",f"- Model: `{settings.model}`",f"- Run time: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",f"- Same user request: **{REQUEST}**",""]
    for label,prompt,answer in rows: output += [f"## {label}","",f"**System prompt:** {prompt}","","**Model response:**","",answer,""]
    output += ["## Comparison — complete after reviewing the three real responses","","| Version | What improved? | What was missing? |","|---|---|---|","| A — Basic | [Your observation] | [Your observation] |","| B — Role + constraints | [Your observation] | [Your observation] |","| C — Role + structure + example | [Your observation] | [Your observation] |","","Verify accuracy; the most detailed answer is not automatically the best.",""]
    path=ROOT/"docs"/"prompt-comparison-results.md"; path.write_text("\n".join(output),encoding="utf-8"); print(f"Saved real outputs to {path.relative_to(ROOT)}"); return 0
if __name__=="__main__": raise SystemExit(main())
