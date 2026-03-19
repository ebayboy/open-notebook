#!/bin/bash -x
#
#
curl --location 'http://116.198.229.83:8009/v1/embeddings' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer 1F981D0DAF0135FE228C505557A4412F' \
--data '{
	"input": "hello",
	"model": "Qwen3-Embedding-8B"
}'
