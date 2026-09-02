from mcp.server.mcpserver import MCPServer
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize MCPServer
mcp = MCPServer("Clinical_Lab_Analyzer")

HARDCODED_REFERENCE_RANGES = {
    "Ferritin": {"min": 15, "max": 150, "unit": "ug/L"},
    "Hemoglobin": {"min": 12, "max": 15, "unit": "g/dL"},
    "Glukoz": {"min": 70, "max": 100, "unit": "mg/dL"},
    "Kolesterol": {"min": 0, "max": 200, "unit": "mg/dL"}
}

@mcp.tool()
def reference_range_lookup(test_name: str) -> str:
    """Lookup standard adult reference range for a lab test."""
    if test_name in HARDCODED_REFERENCE_RANGES:
        return json.dumps(HARDCODED_REFERENCE_RANGES[test_name])
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return json.dumps({})

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = f"""You are a clinical reference lookup tool. 
Provide the standard adult reference range for the lab test: "{test_name}".
Respond ONLY with a JSON object in this exact schema:
{{
  "min": float,
  "max": float,
  "unit": "string"
}}
If you do not know or it varies too wildly without context, return an empty object {{}}."""
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({})


@mcp.tool()
def explain_results_batch(results_json: str) -> str:
    """Explain a batch of lab results based on explainable AI principles. 
    Accepts JSON string array of lab results. 
    Returns JSON string with explanations and next steps."""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return json.dumps({"error": "No API Key"})

    try:
        batch = json.loads(results_json)
    except Exception:
        return json.dumps({"error": "Invalid input format"})

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = "You are a clinical AI assistant. Explain the following lab results based on the principles of Explainable AI. Users should understand WHY a result was flagged and what it means (not just 'abnormal'). Also suggest actionable next steps.\n\n"
    
    for j, res in enumerate(batch):
        prompt += f"Test {j+1}:\n- Name: {res.get('Test_Name')}\n- Value: {res.get('Result')} {res.get('Unit')}\n- Ref Range: {res.get('Reference_Range')}\n- Severity: {res.get('Severity')}\n\n"
    
    prompt += """
Respond ONLY with a valid JSON object containing a single key "explanations" which maps to an array of objects, one for each test in the exact order provided. Each object must have this schema:
{
  "Explanation": "string (clinically relevant language, explainable AI focus)",
  "Suggested_Next_Steps": "string (actionable next steps)"
}"""
    
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
