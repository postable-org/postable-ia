# postable-ia

Serviço de geração de conteúdo com IA do Postable. Agente especializado em criar posts para redes sociais para pequenas e médias empresas brasileiras, utilizando Google Gemini e análise de tendências em tempo real.

O agente analisa o perfil da marca, pesquisa tendências locais via Google Trends, mapeia gaps competitivos e gera posts em português brasileiro nativos para cada plataforma (Instagram, Facebook, LinkedIn, X), acompanhados de imagem gerada por IA.

---

## Membros da Equipe

| Nome | Função |
|------|--------|
| Fabio Missiaggia Brugnara | Tech Lead |
| Rafael Xavier Oliveira | Dev |
| Luca Guimarães Lodi | Design UI/UX |
| Leonardo Stuart de Almeida Ramalho | Produto |

---

## Tecnologias

- Python 3.11
- Google ADK >= 0.1.0
- FastAPI >= 0.115.0 + Uvicorn >= 0.40.0
- Google Gemini 2.5 Flash (texto) + Gemini 3.1 Flash Image (imagem)
- pytrends (Google Trends)
- Pydantic 2, json-repair, slowapi

---

## Configuração

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (opcional)
- Chave de API do Google ([obter aqui](https://aistudio.google.com/app/apikey))

### Variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GOOGLE_API_KEY` | Sim | Chave do Google AI Studio |
| `TEXT_MODEL` | Não | Modelo de texto (padrão: `gemini-2.5-flash`) |
| `IMAGE_MODEL` | Não | Modelo de imagem (padrão: `gemini-3.1-flash-image-preview`) |
| `PORT` | Não | Porta do servidor (padrão: `8000`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Não | Usar Vertex AI em vez do AI Studio (padrão: `FALSE`) |

---

## Uso

### Com Docker Compose (recomendado)

```bash
docker compose up --build
```

Serviço disponível em `http://localhost:8000`.

### Local

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

uvicorn postable_ia.main:app --host 0.0.0.0 --port 8000
```

### Endpoint

**`POST /generate`** — Gera um post via stream SSE.

Exemplo de request:

```json
{
  "business_profile": {
    "niche": "padaria artesanal",
    "city": "Curitiba",
    "state": "PR",
    "tone": "friendly",
    "brand_name": "Padaria do João",
    "brand_colors": ["#D4A853"],
    "brand_must_avoid": "preço baixo"
  },
  "campaign_brief": {
    "goal": "gerar leads",
    "target_audience": "mães de 30-40 anos",
    "cta_channel": "whatsapp"
  },
  "platform": "instagram",
  "placement": "feed"
}
```

Eventos SSE retornados:

| Evento | Descrição |
|--------|-----------|
| `status` | Progresso em tempo real |
| `result` | JSON com `post_text`, `hashtags`, `cta`, `image_base64`, `gap_analysis`, `trend_data` |
| `done` | Fim do stream |
| `error` | Erro durante geração |

### Testes

```bash
pytest
pytest -v
```

---

## Estrutura do Projeto

```
postable-ia/
├── postable_ia/
│   ├── agent.py       # Agente root (modelo, instruções, tools)
│   ├── tools.py       # fetch_trends(), generate_image()
│   ├── config.py      # Configurações via pydantic-settings
│   └── main.py        # FastAPI app
├── api/routes/
│   └── generate.py    # Handler do endpoint /generate
├── schema/
│   ├── request.py     # GenerateRequest
│   └── response.py    # GenerateResponse
├── tests/
├── .env.example
├── Dockerfile
└── requirements.txt
```

---

## Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](./LICENSE) para mais informações.
