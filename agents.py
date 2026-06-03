from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search , scrape_url 
from dotenv import load_dotenv
import os
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)

load_dotenv()

# Model setup: read model from env so users can override invalid defaults.
preferred = os.getenv("MODEL_NAME")
if not preferred:
    # safer default (non-pro suffix); user can set MODEL_NAME in .env
    preferred = "gemini-1.5"

def _init_llm_with_fallback(model_name: str):
    candidates = [model_name, "gemini-1.5", "gemini-1.0"]
    seen = set()
    last_exc = None
    for m in candidates:
        if not m or m in seen:
            continue
        seen.add(m)
        try:
            candidate_llm = ChatGoogleGenerativeAI(model=m, temperature=0)
            # do a lightweight smoke test to confirm the model supports generation
            try:
                candidate_llm.invoke([("system", "sanity check"), ("human", "ping")])
                return candidate_llm
            except Exception as e:
                last_exc = e
                logger.debug("Model %s invoke failed: %s", m, e)
        except Exception as e:
            last_exc = e
            logger.debug("Model %s failed to initialize: %s", m, e)
    # If we reach here, none of the candidates initialized cleanly.
    # Try discovering a supported model via the public REST models endpoint
    try:
        import requests
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # try .env in project root
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('GOOGLE_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                api_key = None

        if api_key:
            url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
            logger.debug('Querying models endpoint to find supported models')
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for mi in data.get('models', []):
                    methods = mi.get('supportedGenerationMethods', []) or mi.get('supported_generation_methods', [])
                    if 'generateContent' in methods:
                        # model resource name is like 'models/gemini-2.5-pro'
                        name = mi.get('name', '')
                        if '/' in name:
                            candidate = name.split('/', 1)[1]
                        else:
                            candidate = name
                        if candidate and candidate not in seen:
                            try:
                                logger.debug('Trying discovered model: %s', candidate)
                                return ChatGoogleGenerativeAI(model=candidate, temperature=0)
                            except Exception as e:
                                last_exc = e
                                logger.debug('Discovered model %s failed: %s', candidate, e)
    except Exception as _rerr:
        logger.debug('Model discovery via REST failed: %s', _rerr)
    msg = (
        "Failed to initialize a working Google generative model.\n"
        "Set a valid model name in the MODEL_NAME environment variable (or .env).\n"
        "You can call ModelService.ListModels to see available models and their supported methods.\n"
        "Last error: %s"
    ) % (last_exc,)
    raise RuntimeError(msg)

# instantiate llm (may raise with helpful guidance)
llm = _init_llm_with_fallback(preferred)


#1st agent - search wrapper
def build_search_agent():
    return lambda query: web_search.invoke(query)

#2nd agent - reader wrapper

def build_reader_agent():
    return lambda url: scrape_url.invoke(url)


#writer chain 

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain 

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()

