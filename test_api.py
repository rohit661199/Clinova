import requests
import json

data = {
    "results": [
        {
            "Test_Name": "Ferritin",
            "Result": "10.0",
            "Unit": "ug/L",
            "Reference_Range": "15-150",
            "Min_Reference": 15,
            "Max_Reference": 150
        }
    ]
}

response = requests.post("http://localhost:8000/analyze_labs", json=data)
print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))
