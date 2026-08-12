from datetime import datetime

from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = "sqlite:///./history.db"
engine = create_engine(DATABASE_URL, echo=False)


class RequestRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    request_type: str          # "summarize" or "classify"
    input_text: str
    output_json: str           # store the result as a JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)


def init_db():
    SQLModel.metadata.create_all(engine)


def save_record(request_type: str, input_text: str, output_json: str):
    with Session(engine) as session:
        record = RequestRecord(
            request_type=request_type,
            input_text=input_text,
            output_json=output_json,
        )
        session.add(record)
        session.commit()


def get_history(limit: int = 20):
    with Session(engine) as session:
        from sqlmodel import select
        statement = select(RequestRecord).order_by(RequestRecord.id.desc()).limit(limit)
        return session.exec(statement).all()