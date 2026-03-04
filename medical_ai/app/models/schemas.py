from typing import List, Optional
from pydantic import BaseModel

class MedicalEntityOut(BaseModel):
    text: str
    entity_type: str
    severity: str
    explanation: str
    value: Optional[str] = None
    unit: Optional[str] = None

class MedicalNERResponse(BaseModel):
    text: str
    entities: List[MedicalEntityOut]