import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from models import LabResultInput, AnalyzedResult

load_dotenv()

# Basic reference dict as requested by "Optional Tool: Call reference_range_lookup(test_name) if test not in hardcoded dict"
HARDCODED_REFERENCE_RANGES = {
    "Ferritin": {"min": 15, "max": 150, "unit": "ug/L"},
    "Hemoglobin": {"min": 12, "max": 15, "unit": "g/dL"},
    "Glukoz": {"min": 70, "max": 100, "unit": "mg/dL"},
    "Kolesterol": {"min": 0, "max": 200, "unit": "mg/dL"}
}

def reference_range_lookup(test_name: str):
    """Optional tool to lookup reference ranges if missing using LLM."""
    # First check hardcoded dictionary
    if test_name in HARDCODED_REFERENCE_RANGES:
        return HARDCODED_REFERENCE_RANGES[test_name]
    
    # If not in hardcoded dict, use LLM to estimate the reference range
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return None

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
If you do not know or it varies too wildly without context, return an empty object {{}}.
"""
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200
        )
        
        data = json.loads(response.choices[0].message.content)
        if "min" in data and "max" in data:
            return {
                "min": float(data["min"]),
                "max": float(data["max"]),
                "unit": data.get("unit", "")
            }
    except Exception as e:
        print(f"Reference range lookup failed for {test_name}: {e}")
        
    return None

def classify_result(result: LabResultInput) -> str:
    """Classify the lab result into Normal, Warning, or Critical."""
    try:
        # Check if the result is a number
        val = float(result.Result)
        
        # Determine min and max reference
        min_ref = result.Min_Reference
        max_ref = result.Max_Reference
        
        if min_ref is None or max_ref is None:
            # Try to lookup
            lookup = reference_range_lookup(result.Test_Name)
            if lookup:
                min_ref = lookup["min"]
                max_ref = lookup["max"]
                
        if min_ref is not None and max_ref is not None:
            if min_ref <= val <= max_ref:
                return "Normal"
            else:
                # Basic heuristic: if it's > 50% out of bounds, Critical, else Warning
                range_span = max_ref - min_ref
                if range_span == 0:
                    range_span = 1 # avoid div by zero
                
                if val < min_ref:
                    deviation = (min_ref - val) / range_span
                else:
                    deviation = (val - max_ref) / range_span
                    
                if deviation > 0.5:
                    return "Critical"
                else:
                    return "Warning"
    except ValueError:
        pass # Not a number, handle text results
    
    # Text results classification (heuristic for strips)
    text_val = str(result.Result).lower()
    if text_val in ["normal", "negatif", "negative"]:
        return "Normal"
    if "pozitif" in text_val or "positive" in text_val or "+" in text_val:
        # Check reference range string if it implies Negative is normal
        if result.Reference_Range and "negatif" in result.Reference_Range.lower():
            return "Warning" # Could be critical depending on the test, but default to warning
    
    return "Warning" # Default fallback if we can't classify

def route_results(analyzed_results: list[AnalyzedResult]) -> list[AnalyzedResult]:
    """Group results by severity (Critical first, then Warning, then Normal)."""
    severity_order = {"Critical": 0, "Warning": 1, "Normal": 2}
    return sorted(analyzed_results, key=lambda x: severity_order.get(x.Severity, 3))

def explain_results(results: list[AnalyzedResult]):
    """Call LLM to generate clinical explanation and next steps."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        for res in results:
            res.Explanation = f"Result is {res.Severity} based on reference ranges."
            res.Suggested_Next_Steps = "Consult your doctor."
        return results

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Process in batches to avoid token limit / truncated JSON issues
    BATCH_SIZE = 10
    
    for i in range(0, len(results), BATCH_SIZE):
        batch = results[i:i + BATCH_SIZE]
        
        prompt = "You are a clinical AI assistant. Explain the following lab results based on the principles of Explainable AI. Users should understand WHY a result was flagged and what it means (not just 'abnormal'). Also suggest actionable next steps.\n\n"
        
        for j, res in enumerate(batch):
            prompt += f"Test {j+1}:\n- Name: {res.Test_Name}\n- Value: {res.Result} {res.Unit}\n- Ref Range: {res.Reference_Range}\n- Severity: {res.Severity}\n\n"
        
        prompt += """
Respond ONLY with a valid JSON object containing a single key "explanations" which maps to an array of objects, one for each test in the exact order provided. Each object must have this schema:
{
  "Explanation": "string (clinically relevant language, explainable AI focus)",
  "Suggested_Next_Steps": "string (actionable next steps)"
}
        """
        
        try:
            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            data = json.loads(response_text)
            explanation_data = data.get("explanations", [])
            
            for j, res in enumerate(batch):
                if j < len(explanation_data):
                    res.Explanation = explanation_data[j].get("Explanation", "Could not generate explanation.")
                    res.Suggested_Next_Steps = explanation_data[j].get("Suggested_Next_Steps", "Consult your doctor.")
                    
        except Exception as e:
            print(f"LLM Explanation failed for batch starting at {i}: {e}")
            for res in batch:
                res.Explanation = f"Result is {res.Severity}. (LLM explanation failed)"
                res.Suggested_Next_Steps = "Consult your healthcare provider."
            
    return results

def process_labs(lab_inputs: list[LabResultInput]) -> list[AnalyzedResult]:
    analyzed_results = []
    
    for lab in lab_inputs:
        severity = classify_result(lab)
        
        # Build reference range string if missing
        ref_str = lab.Reference_Range
        if not ref_str:
            if lab.Min_Reference is not None and lab.Max_Reference is not None:
                ref_str = f"{lab.Min_Reference}-{lab.Max_Reference}"
            else:
                ref_str = "N/A"
                
        analyzed_results.append(
            AnalyzedResult(
                Test_Name=lab.Test_Name,
                Result=str(lab.Result),
                Unit=lab.Unit or "",
                Reference_Range=ref_str,
                Severity=severity,
                Explanation="", # Will be filled by explain_results
                Suggested_Next_Steps="" # Will be filled by explain_results
            )
        )
    
    # Explain (LLM)
    analyzed_results = explain_results(analyzed_results)
    
    # Route (Sort)
    routed_results = route_results(analyzed_results)
    
    return routed_results
