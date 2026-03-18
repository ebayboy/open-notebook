#!/bin/bash -x

curl --location 'http://116.198.229.83:9998/v1/chat/completions' \
--header 'Content-Type: application/json' \
--data '{
  "model": "baidu/ERNIE-4.5-21B-A3B-PT",
  "messages": [
    {
      "role": "user",
      "content": "hello"
    }
  ],
  "temperature": 0.1,
  "extra_body": {
    "chat_template_kwargs": {
      "enable_thinking": false
    }
  }
}'
