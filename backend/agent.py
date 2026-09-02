import os
import json
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from models import LabResultInput, AnalyzedResult

load_dotenv()

async def call_mcp_tool(tool_name: str, args: dict):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(base_dir, "mcp_server.py")
    
    server_params = StdioServerParameters(
        command="python",
        args=[server_script],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=args)
            return result.content[0].text

async def reference_range_lookup(test_name: str):
    """Call MCP tool to lookup reference ranges."""
    try:
        response_str = await call_mcp_tool("reference_range_lookup", {"test_name": test_name})
        data = json.loads(response_str)
        if "min" in data and "max" in data:
            return {
                "min": float(data["min"]),
                "max": float(data["max"]),
                "unit": data.get("unit", "")
            }
    except Exception as e:
        print(f"Reference range lookup failed for {test_name}: {e}")
    return None

async def classify_result(result: LabResultInput) -> str:
    """Classify the lab result into Normal, Warning, or Critical."""
    try:
        val = float(result.Result)
        min_ref = result.Min_Reference
        max_ref = result.Max_Reference
        
        if min_ref is None or max_ref is None:
            lookup = await reference_range_lookup(result.Test_Name)
            if lookup:
                min_ref = lookup["min"]
                max_ref = lookup["max"]
                
        if min_ref is not None and max_ref is not None:
            if min_ref <= val <= max_ref:
                return "Normal"
            else:
                range_span = max_ref - min_ref
                if range_span == 0:
                    range_span = 1
                
                if val < min_ref:
                    deviation = (min_ref - val) / range_span
                else:
                    deviation = (val - max_ref) / range_span
                    
                if deviation > 0.5:
                    return "Critical"
                else:
                    return "Warning"
    except ValueError:
        pass
    
    text_val = str(result.Result).lower()
    if text_val in ["normal", "negatif", "negative"]:
        return "Normal"
    if "pozitif" in text_val or "positive" in text_val or "+" in text_val:
        if result.Reference_Range and "negatif" in result.Reference_Range.lower():
            return "Warning"
    
    return "Warning"

def route_results(analyzed_results: list[AnalyzedResult]) -> list[AnalyzedResult]:
    severity_order = {"Critical": 0, "Warning": 1, "Normal": 2}
    return sorted(analyzed_results, key=lambda x: severity_order.get(x.Severity, 3))

async def explain_results(results: list[AnalyzedResult]):
    """Call MCP tool to generate clinical explanation and next steps."""
    BATCH_SIZE = 10
    
    for i in range(0, len(results), BATCH_SIZE):
        batch = results[i:i + BATCH_SIZE]
        batch_dicts = [res.model_dump() for res in batch]
        
        try:
            response_str = await call_mcp_tool("explain_results_batch", {"results_json": json.dumps(batch_dicts)})
            data = json.loads(response_str)
            
            if "error" in data:
                raise Exception(data["error"])
                
            explanation_data = data.get("explanations", [])
            
            for j, res in enumerate(batch):
                if j < len(explanation_data):
                    res.Explanation = explanation_data[j].get("Explanation", "Could not generate explanation.")
                    res.Suggested_Next_Steps = explanation_data[j].get("Suggested_Next_Steps", "Consult your doctor.")
                    
        except Exception as e:
            print(f"LLM Explanation failed via MCP for batch starting at {i}: {e}")
            for res in batch:
                res.Explanation = f"Result is {res.Severity}. (LLM explanation failed via MCP)"
                res.Suggested_Next_Steps = "Consult your healthcare provider."
            
    return results

async def process_labs(lab_inputs: list[LabResultInput]) -> list[AnalyzedResult]:
    analyzed_results = []
    
    for lab in lab_inputs:
        severity = await classify_result(lab)
        
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
                Explanation="", 
                Suggested_Next_Steps="" 
            )
        )
    
    analyzed_results = await explain_results(analyzed_results)
    routed_results = route_results(analyzed_results)
    
    return routed_results
