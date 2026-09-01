import httpx
import json

def test_vapi_webhook():
    url = "http://localhost:8000/voice/tool-call"
    headers = {
        "Content-Type": "application/json",
        "x-webhook-secret": "mwstesting"
    }

    # Simulate Vapi's payload for registering a patient
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_12345",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Test",
                            "last_name": "User",
                            "date_of_birth": "1985-10-15",
                            "sex": "Female",
                            "phone_number": "5551239999",
                            "address_line_1": "456 Test St",
                            "city": "Testville",
                            "state": "NY",
                            "zip_code": "10001"
                        }
                    }
                }
            ]
        }
    }

    print(f"Sending POST request to {url}")
    print("Headers:", headers)
    print("Payload:", json.dumps(payload, indent=2))
    print("-" * 40)

    try:
        response = httpx.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    test_vapi_webhook()
