from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    fullname: str
    email: str
    phone: str
    user_type: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenLogout(BaseModel):
    refresh_token: str


class DocUploadResponse(BaseModel):
    doc_id: int
    filename: str

class QARequest(BaseModel):
    doc_id: int
    question: str

class Question(BaseModel):
    document_id: str
    question: str


class Question_r(BaseModel):
    document_id: str
    question: str = ""
    prompt_type: str = "summarize"
    custom_query: str = ""

class Hr_Question(BaseModel):
    question: str