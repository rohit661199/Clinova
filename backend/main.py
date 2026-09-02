from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import LabAnalysisRequest, LabAnalysisResponse
from agent import process_labs
import uvicorn

app = FastAPI(title="Clinical Lab Results Analyzer API")

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze_labs", response_model=LabAnalysisResponse)
async def analyze_labs_endpoint(request: LabAnalysisRequest):
    if not request.results:
        raise HTTPException(status_code=400, detail="No lab results provided.")
        
    try:
        analyzed_results = await process_labs(request.results)
        return LabAnalysisResponse(analyzed_results=analyzed_results)
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during lab analysis.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
