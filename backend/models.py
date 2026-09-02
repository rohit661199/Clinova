from pydantic import BaseModel, Field
from typing import List, Optional

class LabResultInput(BaseModel):
    Test_Name: str
    Result: str
    Unit: Optional[str] = None
    Reference_Range: Optional[str] = None
    Min_Reference: Optional[float] = None
    Max_Reference: Optional[float] = None

class LabAnalysisRequest(BaseModel):
    results: List[LabResultInput]

class AnalyzedResult(BaseModel):
    Test_Name: str
    Result: str
    Unit: str
    Reference_Range: str
    Severity: str # "Critical", "Warning", "Normal"
    Explanation: str
    Suggested_Next_Steps: str

class LabAnalysisResponse(BaseModel):
    analyzed_results: List[AnalyzedResult]
