# Adoption Copilot

**Agentic AI for Context-Aware, Hyper-Personalized Digital Banking**

*🚀 "Awareness isn't the gap — activation is."*

## The problem

Customers often already know about features like AutoPay, SIPs, and
Insurance AutoPay — but never activate them, due to fear of losing
money, low digital literacy, financial jargon, and lack of
native-language support. Existing nudges are untimed, impersonal, and
easy to ignore.

## The solution

An agentic Digital Adoption Copilot that:

1. **Detects** the exact moment a customer would benefit from a
   digital feature (from their transaction patterns).
2. **Engages** them in a short, plain-language conversation.
3. **Clarifies** doubts and objections, in simple terms.
4. **Activates** the feature — but only with explicit, unambiguous
   consent.

We have built this as an MVP prototype for IIC 3.0. Here, we have used Gradio for UI, no
voice, mock `.txt` data instead of a real database, and a rules-based
trigger engine instead of a trai

## Architecture

```
adoption-copilot/
├── app.py                    
├── requirements.txt
├── .env.example
├── data/
│   ├── customer.txt          
│   ├── transactions.txt      
│   └── banking_features.txt  
├── prompts/
│   ├── system_prompt.py      
│   └── evaluator_prompt.py   
├── models/
│   ├── customer.py           
│   └── evaluation.py         
├── agent/
│   ├── chat.py                
│   ├── tools.py                
│   ├── tool_handler.py         
│   ├── evaluator.py            
│   └── rerun.py                
├── backend/
│   ├── data_loader.py          
│   ├── trigger_engine.py       
│   ├── activation.py           
│   └── logger.py               
├── gradio_ui/
│   └── interface.py            
└── utils/
    ├── llm.py                  
    ├── constants.py
    └── helpers.py
```

## How it works

- **Trigger engine**: reads a customer's profile + transaction history
  and applies simple rules (e.g. 3+ manual bill payments and no
  AutoPay -> flag AutoPay) to detect a relevant opportunity.
- **Agent**: an LLM with tool-calling access to the trigger engine,
  the feature knowledge base, and a mock activation function. It
  follows the system prompt's Detect -> Engage -> Clarify -> Activate
  flow, and never activates without explicit consent in the
  conversation.
- **Evaluator**: after each agent turn, a second LLM call checks the
  response against a 10-point rubric (factual consistency, no jargon,
  consent before activation, no hallucination, tone, etc.) and returns
  a structured `Evaluation`. If it fails, `agent/rerun.py` retries the
  turn (up to `MAX_RETRIES`) with the evaluator's feedback injected as
  guidance.

## Model

Uses [Google AI Studio](https://aistudio.google.com) with the model
`gemini-3.5-flash-lite`, via Google's OpenAI-compatible endpoint (the `openai` SDK is just pointed
at Google). Both the main agent and the evaluator use the
same model and client.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your Google AI Studio API key
# get a key at https://aistudio.google.com/apikey

python app.py
```

Gradio will print a local URL (and optionally a public share link) to
open in your browser.

## Demo flow

1. Pick a customer from the dropdown:
   - **Rahul Sharma** — repeated manual electricity bills -> AutoPay
   - **Priya Verma** — recurring salary credits, no SIP -> SIP
   - **Amit Singh** — repeated manual insurance premiums -> Insurance
     AutoPay
2. The Copilot opens with a short, personalized greeting and surfaces
   the detected opportunity in plain language.
3. Ask questions, raise objections — the Copilot answers using the
   feature knowledge base.
4. Say something like "yes, go ahead" to give explicit consent — the
   Copilot calls the activation tool and confirms.

## Notes / scope

- No real banking backend — activation is simulated in
  `backend/activation.py`.
- No voice/STT/TTS in this MVP; text chat only.
- Data lives in flat `.txt` files under `data/`, not a database.
