# The Writer's Room — Phase 1
## Autonomous Story and Image Generation Layer

### Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate`
3. Install dependencies: `pip install langgraph langchain langchain-openai langchain-community openai chromadb python-dotenv pillow requests langchain-groq groq`
4. Create `.env` file with: `GROQ_API_KEY=your_key_here`

### Run
```cmd
python main.py
```

### Modes
- **Mode 1 (Auto):** Enter a story idea, AI generates full screenplay
- **Mode 2 (Manual):** Validates a pre-written script structure

### System Architecture
- **MCP Registry:** All tools registered and discovered dynamically (no hardcoding)
- **LangGraph StateGraph:** 7 nodes with conditional routing
- **ChromaDB:** Persistent vector memory for all agents
- **Pollinations.ai:** Free image generation (no API key needed)

### Agents
1. **Scriptwriter Agent** — generates structured screenplay from prompt
2. **Script Validator Agent** — validates manually uploaded scripts
3. **Human-in-the-Loop Agent** — checkpoint for human approval/rejection
4. **Character Designer Agent** — extracts rich character profiles
5. **Image Synthesizer Agent** — generates character portrait images

### Outputs
- `outputs/scene_manifest.json` — full structured screenplay
- `outputs/character_db.json` — character profiles with image paths
- `outputs/images/` — AI-generated character portraits

### Tech Stack
- LangGraph (stateful workflow)
- Groq API / Llama-3.3-70b (LLM)
- ChromaDB (vector memory)
- Pollinations.ai (image generation)
- Python 3.10+