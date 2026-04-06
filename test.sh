curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "req-001",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "unique-msg-id-001", 
        "parts": [
          {
            "kind": "text", 
            "text": "which venodrs are selling Fertilizers "
          }
        ]
      }
    }
  }'