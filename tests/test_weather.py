import httpx
from agentic_assistant.tools import get_weather

class FakeResponse:
    def __init__(self,payload): self.payload=payload
    def raise_for_status(self): return None
    def json(self): return self.payload

def test_weather_geocoding_then_forecast(monkeypatch):
    calls=[]
    def fake_get(url,params,timeout):
        calls.append((url,params))
        if "geocoding" in url: return FakeResponse({"results":[{"name":"Multan","country":"Pakistan","latitude":30.2,"longitude":71.4}]})
        return FakeResponse({"current":{"temperature_2m":25},"current_units":{"temperature_2m":"°C"},"timezone":"Asia/Karachi"})
    monkeypatch.setattr(httpx,"get",fake_get)
    result=get_weather("Multan")
    assert result["location"]["name"]=="Multan"
    assert result["current"]["temperature_2m"]==25
    assert len(calls)==2
