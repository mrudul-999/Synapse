from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

plan: List[str] = Field(default_factory=list)

plan.append("hello")


print(plan)
