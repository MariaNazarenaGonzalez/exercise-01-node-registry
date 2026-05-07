
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from .database import Base, engine, get_db
from .models import Node
from .schemas import NodeCreate, NodeUpdate, NodeResponse, HealthResponse

app = FastAPI()


def wait_for_db():
    for _ in range(20):  # intenta 20 veces
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Database not ready after waiting")


@app.on_event("startup")
def startup_event():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        count = db.query(Node).filter(Node.status == "active").count()
        return {"status": "ok", "db": "connected", "nodes_count": count}
    except Exception:
        return {"status": "ok", "db": "disconnected", "nodes_count": 0}


@app.post("/api/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(node: NodeCreate, db: Session = Depends(get_db)):
    existing = db.query(Node).filter(Node.name == node.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Node already exists")

    new_node = Node(
        name=node.name,
        host=node.host,
        port=node.port,
        status="active"
    )

    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node


@app.get("/api/nodes", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(Node).filter(Node.status == "active").all()


@app.get("/api/nodes/{name}", response_model=NodeResponse)
def get_node(name: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.put("/api/nodes/{name}", response_model=NodeResponse)
def update_node(name: str, data: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if data.host is not None:
        node.host = data.host
    if data.port is not None:
        node.port = data.port

    db.commit()
    db.refresh(node)
    return node


@app.delete("/api/nodes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(name: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.status = "inactive"
    db.commit()
    return None