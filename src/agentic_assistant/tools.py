"""Local tools exposed to the model. Every tool validates its input before execution."""
from __future__ import annotations
import ast, math, operator, sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Type
import httpx
from pydantic import BaseModel, ValidationError
from .models import CalculatorArgs, SaveNoteArgs, SearchNotesArgs, WeatherArgs

_BINARY_OPERATORS = {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow}
_UNARY_OPERATORS = {ast.UAdd:operator.pos,ast.USub:operator.neg}
_MATH_FUNCTIONS = {"sqrt":math.sqrt,"sin":math.sin,"cos":math.cos,"tan":math.tan,"log":math.log,"log10":math.log10,"abs":abs,"ceil":math.ceil,"floor":math.floor}

def _safe_calculate(expression: str) -> float:
    if len(expression)>200: raise ValueError("Expression is too long.")
    try: parsed=ast.parse(expression,mode="eval")
    except SyntaxError as exc: raise ValueError("Invalid arithmetic expression.") from exc
    def visit(node: ast.AST) -> float:
        if isinstance(node,ast.Expression): return visit(node.body)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            value=float(node.value)
            if not math.isfinite(value): raise ValueError("Only finite numbers are allowed.")
            return value
        if isinstance(node,ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left,right=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Pow) and abs(right)>12: raise ValueError("Exponent magnitude is limited to 12.")
            result=_BINARY_OPERATORS[type(node.op)](left,right)
            if not math.isfinite(float(result)) or abs(result)>1e100: raise ValueError("Calculation result is outside the supported range.")
            return float(result)
        if isinstance(node,ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS: return float(_UNARY_OPERATORS[type(node.op)](visit(node.operand)))
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            fn=_MATH_FUNCTIONS.get(node.func.id)
            if fn is None or len(node.args)!=1 or node.keywords: raise ValueError("Only approved one-argument math functions are allowed.")
            return float(fn(visit(node.args[0])))
        raise ValueError(f"Unsupported expression element: {type(node).__name__}.")
    try: result=visit(parsed)
    except ZeroDivisionError as exc: raise ValueError("Division by zero is not allowed.") from exc
    except (OverflowError,ValueError) as exc: raise ValueError(str(exc)) from exc
    return int(result) if result.is_integer() else result

def calculate(expression: str) -> dict[str,Any]:
    """Safely evaluate arithmetic without executing arbitrary Python."""
    return {"expression":expression,"result":_safe_calculate(expression)}

def get_weather(city: str, units: str="celsius") -> dict[str,Any]:
    """Get current weather from Open-Meteo geocoding and forecast APIs."""
    if units not in {"celsius","fahrenheit"}: raise ValueError("units must be 'celsius' or 'fahrenheit'.")
    geo=httpx.get("https://geocoding-api.open-meteo.com/v1/search",params={"name":city,"count":1,"language":"en","format":"json"},timeout=15.0)
    geo.raise_for_status(); places=geo.json().get("results") or []
    if not places: raise ValueError(f"No location found for '{city}'.")
    place=places[0]; temp="fahrenheit" if units=="fahrenheit" else "celsius"; wind="mph" if units=="fahrenheit" else "kmh"
    response=httpx.get("https://api.open-meteo.com/v1/forecast",params={"latitude":place["latitude"],"longitude":place["longitude"],"current":"temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m","temperature_unit":temp,"wind_speed_unit":wind,"timezone":"auto"},timeout=15.0)
    response.raise_for_status(); payload=response.json(); current=payload.get("current")
    if not isinstance(current,dict): raise ValueError("Open-Meteo did not return current weather data.")
    return {"location":{"name":place.get("name"),"admin1":place.get("admin1"),"country":place.get("country")},"current":current,"units":payload.get("current_units",{}),"timezone":payload.get("timezone"),"source":"Open-Meteo"}

class NotesStore:
    """SQLite notes store, initialized automatically."""
    def __init__(self,database_path:Path|str=".data/notes.db"):
        self.database_path=Path(database_path); self.database_path.parent.mkdir(parents=True,exist_ok=True); self._initialize()
    def _connect(self):
        connection=sqlite3.connect(self.database_path,timeout=10); connection.row_factory=sqlite3.Row; return connection
    def _initialize(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)")
    def save(self,title:str,content:str)->dict[str,Any]:
        title,content=title.strip(),content.strip()
        if not title or not content: raise ValueError("Both title and content are required.")
        created=datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as db:
            cursor=db.execute("INSERT INTO notes(title,content,created_at) VALUES(?,?,?)",(title,content,created)); note_id=int(cursor.lastrowid)
        return {"saved":True,"note_id":note_id,"title":title,"created_at":created}
    def search(self,query:str,limit:int=10)->dict[str,Any]:
        query=query.strip()
        if not query: raise ValueError("Search query cannot be empty.")
        terms=[part for part in query.split() if part]; where=" OR ".join("(title LIKE ? OR content LIKE ?)" for _ in terms); params=[]
        for term in terms:
            escaped=term.replace("\\","\\\\").replace("%","\\%").replace("_","\\_"); params.extend([f"%{escaped}%",f"%{escaped}%"])
        params.append(max(1,min(limit,20)))
        with self._connect() as db:
            rows=db.execute(f"SELECT id,title,content,created_at FROM notes WHERE {where} ORDER BY id DESC LIMIT ?",params).fetchall()
        return {"query":query,"count":len(rows),"notes":[dict(row) for row in rows]}

@dataclass(frozen=True)
class ToolDefinition:
    name:str
    description:str
    args_model:Type[BaseModel]
    function:Callable[...,dict[str,Any]]
    def openai_schema(self):
        schema=self.args_model.model_json_schema(); schema.pop("title",None); schema.pop("$defs",None)
        return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":schema}}
    def execute(self,raw_arguments:str)->dict[str,Any]:
        try:
            args=self.args_model.model_validate_json(raw_arguments); return self.function(**args.model_dump())
        except ValidationError as exc: return {"error":"Invalid tool arguments","details":exc.errors(include_url=False)}
        except Exception as exc: return {"error":type(exc).__name__,"message":str(exc)}

class ToolRegistry:
    def __init__(self,tools:list[ToolDefinition]):
        self._tools={tool.name:tool for tool in tools}
        if len(self._tools)!=len(tools): raise ValueError("Tool names must be unique.")
    @property
    def definitions(self): return list(self._tools.values())
    def openai_schemas(self): return [tool.openai_schema() for tool in self.definitions]
    def execute(self,name:str,arguments:str):
        tool=self._tools.get(name)
        return tool.execute(arguments) if tool else {"error":"Unknown tool","tool":name}

def build_registry(database_path:Path|str=".data/notes.db")->ToolRegistry:
    notes=NotesStore(database_path)
    return ToolRegistry([
        ToolDefinition("get_weather","Look up current weather for a city using Open-Meteo. Never guess weather.",WeatherArgs,get_weather),
        ToolDefinition("calculate","Safely calculate arithmetic. Use for exact results.",CalculatorArgs,calculate),
        ToolDefinition("save_note","Save a titled note to local SQLite when asked to remember something.",SaveNoteArgs,notes.save),
        ToolDefinition("search_notes","Search saved SQLite notes.",SearchNotesArgs,notes.search),
    ])
