from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

app = FastAPI()

# Разрешить CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде заменить на адрес сайта
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# В памяти храним активные матчи
matches = {}

class StartMatchRequest(BaseModel):
    players: list[str]

class PointRequest(BaseModel):
    match_id: str
    player: int  # 0 или 1

class UndoRequest(BaseModel):
    match_id: str

@app.post("/match/start")
def start_match(req: StartMatchRequest):
    match_id = str(uuid4())
    matches[match_id] = {
        "players": req.players,
        "sets": [[0, 0]],
        "game_score": [0, 0],
        "history": [],
        "start_time": datetime.utcnow().isoformat()
    }
    return {"match_id": match_id}

@app.post("/match/point")
def add_point(req: PointRequest):
    match = matches.get(req.match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    if req.player not in (0, 1):
        raise HTTPException(status_code=400, detail="Неверный игрок")

    match["game_score"][req.player] += 1
    match["history"].append({
        "point": req.player,
        "time": datetime.utcnow().isoformat()
    })
    return {"status": "ok"}

@app.post("/match/undo")
def undo_point(req: UndoRequest):
    match = matches.get(req.match_id)
    if not match or not match["history"]:
        raise HTTPException(status_code=404, detail="Нет истории или матча")

    last = match["history"].pop()
    match["game_score"][last["point"]] = max(0, match["game_score"][last["point"]] - 1)
    return {"status": "undone"}

@app.get("/match/{match_id}")
def get_match(match_id: str):
    match = matches.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")
    return {
        "players": match["players"],
        "sets": match["sets"],
        "game_score": match["game_score"],
        "history": match["history"],
        "start_time": match["start_time"]
    }

@app.get("/match/{match_id}/export")
def export_match(match_id: str):
    match = matches.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")
    return {
        "match_id": match_id,
        "players": match["players"],
        "score": {
            "set1": match["sets"][0],
        },
        "current_game_score": f"{match['game_score'][0]}-{match['game_score'][1]}",
        "start_time": match["start_time"],
        "events": [
            {"point": i+1, "winner": match["players"][e["point"]], "timestamp": e["time"]}
            for i, e in enumerate(match["history"])
        ],
        "status": "in_progress"
    }
