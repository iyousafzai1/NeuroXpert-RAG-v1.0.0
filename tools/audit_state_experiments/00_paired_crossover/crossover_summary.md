# Paired verifier crossover on byte-identical extracted records

| extractor | condition | row set (sha256[:12]) | verifier | source of verdict | keep/revise/drop | overclaim /100 |
|---|---|---|---|---|---|---|
| llama31_8b | B | archived (f86deee0acae) | llama-3.1-8b-instruct | original run | 50/36/14 | 2 |
| llama31_8b | B | archived (f86deee0acae) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 50/36/14 | 2 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 98/100 | overclaim flags identical 100/100 |
| llama31_8b | B | clean (e2d6a2b41e8e) | llama-3.1-8b-instruct | original run | 51/36/13 | 2 |
| llama31_8b | B | clean (e2d6a2b41e8e) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 50/37/13 | 2 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 99/100 | overclaim flags identical 100/100 |
| llama31_8b | C | archived (68c7a06af726) | llama-3.1-8b-instruct | original run | 63/27/10 | 4 |
| llama31_8b | C | archived (68c7a06af726) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 61/29/10 | 4 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 96/100 | overclaim flags identical 100/100 |
| llama31_8b | C | clean (88b605f26a2e) | llama-3.1-8b-instruct | original run | 66/24/10 | 2 |
| llama31_8b | C | clean (88b605f26a2e) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 64/26/10 | 2 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 96/100 | overclaim flags identical 100/100 |
| qwen25_7b | B | archived (845ae9450989) | qwen2.5-7b-instruct | original run | 18/53/29 | 79 |
| qwen25_7b | B | archived (845ae9450989) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 54/38/8 | 0 |
| qwen25_7b | B | archived (845ae9450989) | qwen2.5-7b-instruct | fresh (vLLM) self = qwen | 18/53/29 | 81 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 98/100 | overclaim flags identical 98/100 |
| qwen25_7b | B | clean (d111b7edee19) | llama-3.1-8b-instruct | original run | 55/35/10 | 1 |
| qwen25_7b | B | clean (d111b7edee19) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 57/34/9 | 0 |
| qwen25_7b | B | clean (d111b7edee19) | qwen2.5-7b-instruct | fresh (vLLM) self = qwen | 17/55/28 | 79 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 95/100 | overclaim flags identical 98/100 |
| qwen25_7b | C | archived (0cc04e79e3b5) | qwen2.5-7b-instruct | original run | 40/55/5 | 64 |
| qwen25_7b | C | archived (0cc04e79e3b5) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 64/30/6 | 1 |
| qwen25_7b | C | archived (0cc04e79e3b5) | qwen2.5-7b-instruct | fresh (vLLM) self = qwen | 41/54/5 | 62 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 97/100 | overclaim flags identical 92/100 |
| qwen25_7b | C | clean (daac88579e5a) | llama-3.1-8b-instruct | original run | 71/24/5 | 0 |
| qwen25_7b | C | clean (daac88579e5a) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 70/25/5 | 0 |
| qwen25_7b | C | clean (daac88579e5a) | qwen2.5-7b-instruct | fresh (vLLM) self = qwen | 44/51/5 | 66 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 99/100 | overclaim flags identical 100/100 |
| mistral7b | B | archived (eb4548418e02) | mistral-7b-instruct-v0.3 | original run | 49/46/5 | 1 |
| mistral7b | B | archived (eb4548418e02) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 53/32/15 | 0 |
| mistral7b | B | archived (eb4548418e02) | mistral-7b-instruct-v0.3 | fresh (vLLM) self = mistral | 49/46/5 | 1 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 100/100 | overclaim flags identical 100/100 |
| mistral7b | B | clean (1a5386cb2bdf) | llama-3.1-8b-instruct | original run | 52/32/16 | 0 |
| mistral7b | B | clean (1a5386cb2bdf) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 52/32/16 | 0 |
| mistral7b | B | clean (1a5386cb2bdf) | mistral-7b-instruct-v0.3 | fresh (vLLM) self = mistral | 48/45/7 | 0 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 100/100 | overclaim flags identical 100/100 |
| mistral7b | C | archived (8f4918b63ccd) | mistral-7b-instruct-v0.3 | original run | 84/12/4 | 0 |
| mistral7b | C | archived (8f4918b63ccd) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 75/19/6 | 1 |
| mistral7b | C | archived (8f4918b63ccd) | mistral-7b-instruct-v0.3 | fresh (vLLM) self = mistral | 85/11/4 | 0 |
|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical 99/100 | overclaim flags identical 100/100 |
| mistral7b | C | clean (7c8b9ded100c) | llama-3.1-8b-instruct | original run | 73/21/6 | 1 |
| mistral7b | C | clean (7c8b9ded100c) | llama-3.1-8b-instruct | fresh (vLLM) Llama | 75/19/6 | 1 |
| mistral7b | C | clean (7c8b9ded100c) | mistral-7b-instruct-v0.3 | fresh (vLLM) self = mistral | 82/14/4 | 0 |
|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical 98/100 | overclaim flags identical 99/100 |
