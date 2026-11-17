from agentic_assistant.tools import NotesStore,_safe_calculate,build_registry

def test_calculator_basic_math():
    assert _safe_calculate("(18 * 7) + 4")==130
    assert _safe_calculate("sqrt(81) + 2")==11

def test_calculator_rejects_code_execution():
    try: _safe_calculate("__import__('os').system('echo unsafe')")
    except ValueError as exc: assert "Unsupported" in str(exc)
    else: raise AssertionError("Unsafe input accepted")

def test_calculator_rejects_large_exponent():
    try: _safe_calculate("2 ** 100")
    except ValueError as exc: assert "Exponent" in str(exc)
    else: raise AssertionError("Large exponent accepted")

def test_notes_save_and_search(tmp_path):
    store=NotesStore(tmp_path/"notes.db"); saved=store.save("Week 1","Agent loop uses tools.")
    found=store.search("agent loop")
    assert saved["saved"] and found["count"]==1 and found["notes"][0]["title"]=="Week 1"

def test_registry_schemas_generated_from_pydantic(tmp_path):
    schemas=build_registry(tmp_path/"notes.db").openai_schemas()
    names={item["function"]["name"] for item in schemas}
    assert names=={"get_weather","calculate","save_note","search_notes"}
    calc=next(item for item in schemas if item["function"]["name"]=="calculate")
    assert "expression" in calc["function"]["parameters"]["properties"]

def test_registry_validation_error(tmp_path):
    assert build_registry(tmp_path/"notes.db").execute("calculate",'{"unknown":"parameter"}')["error"]=="Invalid tool arguments"

def test_registry_unknown_tool(tmp_path):
    assert build_registry(tmp_path/"notes.db").execute("missing","{}")["error"]=="Unknown tool"

def test_calculator_rejects_boolean():
    try: _safe_calculate("True + 1")
    except ValueError as exc: assert "Unsupported" in str(exc)
    else: raise AssertionError("Boolean accepted")
