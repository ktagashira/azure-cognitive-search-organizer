# azure-cognitive-search-organizer

The script extracts text from a website and formats it for Azure Cognitive Search.

## SetUp

```
$ ghq get git@github.com:ktagashira/azure-cognitive-search-organizer.git
$ cd /path/to/this/repo
$ cp .env.sample .env
```

### Prepare credentials

- `AZURE_OPEN_AI_BASE`
- `AZURE_OPEN_AI_API_KEY`  
  Please fill the credentials of Azure OpenAI SERVICE.
- `AZURE_OPEN_AI_DEPLOYMENT`  
  Please fill the model name you want to use.

## Execution

First, please fill the `.env`.

- `URL_FILE_PATH`  
  The path to a CSV containing URLs
- `URL_COLUMNS`  
  CSV URL column
- `CLIENT_NAME`  
  Client name(Used to store the execution results)

```
$ docker-compose up
$ docker-compose exec azure-cognitive-search-organizer /bin/bash
$ poetry run python3 src/main.py
```
