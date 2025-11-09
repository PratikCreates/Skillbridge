# 🚀 SkillBridge: Autonomous AI Career Guidance Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Modal](https://img.shields.io/badge/Deployed%20on-Modal-purple.svg)](https://modal.com/)

**SkillBridge** is an autonomous AI-powered career guidance platform that revolutionizes professional development. Unlike traditional systems relying on keyword matching, SkillBridge builds and reasons over a dynamic, hierarchical knowledge graph of professional skills, autonomously updated from live job market data.

## 🎯 Key Innovation: Inference-Aware Recommendations

Traditional career platforms fail to provide actionable guidance because they rely on simple keyword matching, recommending skills users may already implicitly know. **SkillBridge solves this** - by recognizing that proficiency in PyTorch implies knowledge of Python and Machine Learning, it avoids redundant suggestions and identifies true, actionable skill gaps.

**Result**: 25-33% reduction in redundant recommendations for advanced users, with an average F1-score of 0.81 for knowledge graph quality (0.92 for Data Scientist role).

![SkillBridge Architecture](fig1_improved.png)

---

## ✨ Core Features

### 🤖 Autonomous Knowledge Graph Construction
The **AI Surfer** agent employs a two-stage, multi-agent workflow:
1. **Researcher Agent** (Gemini 2.0 Flash): Search-enabled LLM finds and extracts clean text from recent, high-quality job descriptions
2. **Expert Analyst Agent** (Kimi-K2-Instruct): Powerful reasoning LLM synthesizes data into structured JSON containing 5-7 critical skills, categories, and prerequisite relationships

**Benefits:**
- Daily autonomous updates vs. 6-12 months for traditional systems
- Hierarchical understanding of skill dependencies (e.g., PyTorch → Machine Learning → Python)
- High-fidelity output: 0.92 F1-score for Data Scientist role

### 🧠 Inference-Aware Recommendation Engine
Five-stage pipeline that reasons over the knowledge graph:
1. **Skill Extraction**: Hybrid spaCy + LLM validation
2. **Graph Loading**: Full hierarchical skill graph loaded into NetworkX
3. **Inference**: Traverses graph upwards using `nx.ancestors` to find all implied prerequisite skills
4. **Gap Analysis**: Set difference between (Required Skills) - (Explicit + Inferred Skills)
5. **Path Generation**: Topological sort creates pedagogically sound learning sequence

**Result**: 25-33% reduction in redundant suggestions for advanced users

### 📈 Temporal Trend Forecasting
The **Temporal Engine** tracks skill demand evolution through multi-source data fusion:
- **Stack Exchange API**: Tag counts and question activity as developer interest signals
- **Reddit API**: Community engagement scores from job-related subreddits (r/forhire, r/jobs, r/careerguidance)
- **Prophet Forecasting**: 6-month predictions with 100% success rate for skills with historical data

### ⚡ Production-Ready Architecture
- **Serverless Deployment**: Modal Labs with event-driven functions
- **Distributed Database**: TiDB Cloud for horizontal scalability and ACID compliance
- **Performance**: 50+ concurrent users, ~30s response time, 99.5% uptime
- **Security**: TLS encryption, input validation, zero critical vulnerabilities

---

## 🏗️ System Architecture

SkillBridge is architected as a **dual-loop intelligent system** with four principal zones:

### Zone 1: Data Sources
Multi-source data aggregation:
- Unstructured job descriptions from global employment portals
- Authenticated community APIs (Stack Overflow, Reddit)
- Professional networking data for career progression modeling
- Educational platform datasets for learning resource mapping

### Zone 2: Serverless AI Core
Event-driven autonomous agents on Modal Labs:
- **AI Surfer**: Daily scheduled function for knowledge graph updates
- **Temporal Engine**: Weekly aggregation and forecasting
- **Inference Engine**: Real-time FastAPI endpoints for user requests

### Zone 3: Intelligent Data Store
TiDB Cloud distributed SQL with three logical partitions:
- **Hierarchical Knowledge Graph (HKG)**: Skills, prerequisites, job roles
- **Temporal Data Graph (TDG)**: Chronological skill demand snapshots
- **User Interaction Repository**: Personalized data and recommendation history

### Zone 4: Presentation Layer
- **Streamlit Dashboard**: Interactive visualization of learning paths and trends
- **RESTful API**: Integration with third-party platforms

**System Flow:**
```
Loop 1 (Background): Data Sources → AI Surfer/Temporal Engine → Database
Loop 2 (On-Demand): User Upload → Resume Parser → Inference Engine → Dashboard
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Modal Labs | Serverless Python, API hosting, scheduled functions |
| **Database** | TiDB Cloud | Distributed SQL with ACID compliance |
| **AI Models** | Gemini 2.0, Kimi-K2, Mistral-7B, GPT-4o | Multi-agent knowledge extraction |
| **Frontend** | Streamlit | Interactive dashboard |
| **APIs** | FastAPI | RESTful endpoints |
| **Graph Processing** | NetworkX | Prerequisite traversal and inference |
| **Forecasting** | Prophet | Time-series demand prediction |
| **NLP** | spaCy | Skill extraction and normalization |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Modal CLI configured
- TiDB Cloud account
- API keys: AIML API, Nebius AI, YouTube, Reddit, Stack Exchange

### Installation

```bash
# Clone and setup
git clone https://github.com/your-username/skillbridge-mvp.git
cd skillbridge-mvp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Deploy backend
modal deploy skillbridge/api/main.py

# Initialize knowledge graph (first run)
# Go to Modal dashboard → run_daily_knowledge_graph_update → Run

# Launch frontend
streamlit run streamlit_app/app.py
```

---

## 📊 Validated Performance Metrics

### Knowledge Graph Quality (vs. Ground Truth)
| Role | Precision | Recall | F1-Score |
|------|-----------|--------|----------|
| **Data Scientist** | 0.88 | 0.96 | **0.92** |
| **Frontend Developer** | 0.75 | 0.82 | 0.78 |
| **AI Engineer** | 0.79 | 0.85 | 0.82 |
| **Average** | 0.81 | 0.88 | **0.81** |

### System Performance
| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Recommendation Reduction** | ≥ 20% | 25-33% | ✅ Exceeded |
| **Temporal Forecasting Success** | ≥ 80% | 100% | ✅ Exceeded |
| **Response Time** | ≤ 60s | ~30s | ✅ Exceeded |
| **Concurrent Users** | ≥ 10 | 50+ | ✅ Exceeded |
| **System Uptime** | ≥ 99% | 99.5% | ✅ Exceeded |

---

## 📁 Project Structure

```
skillbridge-mvp/
├── skillbridge/                 # Core application
│   ├── api/main.py              # Modal API & scheduled functions
│   ├── core/                    # Core algorithms
│   │   ├── knowledge_graph_builder.py  # AI Surfer agent
│   │   ├── career_graph.py      # Inference engine
│   │   ├── prediction_engine.py # Prophet forecasting
│   │   └── ...
│   ├── database/                # Database layer
│   ├── processing/              # Data processing
│   └── utils/                   # Utilities
├── streamlit_app/app.py         # Frontend dashboard
├── evaluation/                  # Testing & validation
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🔬 How It Works

### For Users:
1. **Resume Analysis**: Upload resume (PDF/DOCX/TXT) → Hybrid extraction (spaCy + LLM + OCR fallback)
2. **Skill Inference**: System traverses knowledge graph using `nx.ancestors` to identify all implied skills
3. **Gap Analysis**: Computes true gaps = (Required Skills) - (Explicit + Inferred Skills)
4. **Path Generation**: Topological sort on gap subgraph creates optimal learning sequence
5. **Resource Matching**: YouTube + GitHub integration with quality ranking and trend forecasts

### For the System (Autonomous):
1. **Daily AI Surfer**: Researcher agent scrapes job postings → Expert analyst extracts structured skills → Updates knowledge graph
2. **Weekly Temporal Engine**: Queries Stack Overflow + Reddit APIs → Aggregates engagement metrics → Forecasts 6-month trends
3. **Continuous Validation**: Graph validator checks for circular dependencies and category consistency

---

## 💻 Code Examples

### 1. AI Surfer: Autonomous Knowledge Graph Construction

```python
@modal.function(schedule=modal.Cron("0 2 * * *"))
async def run_daily_knowledge_graph_update():
    # Stage 1: Researcher Agent (Gemini)
    job_text = await researcher.search_and_extract("Data Scientist")
    
    # Stage 2: Expert Analyst (Kimi)
    skills = await analyst.synthesize_skills(job_text)
    
    # Update graph
    db_service.update_skill_graph(skills)
```

### 2. Inference-Aware Recommendation Engine

```python
def infer_implicit_skills(explicit_skills: Set[str]) -> Set[str]:
    """Find all implied prerequisites using graph traversal"""
    inferred = set()
    for skill in explicit_skills:
        prerequisites = nx.ancestors(graph, skill)
        inferred.update(prerequisites)
    return inferred

def compute_skill_gaps(explicit_skills, target_role):
    required = get_role_requirements(target_role)
    inferred = infer_implicit_skills(explicit_skills)
    user_profile = explicit_skills | inferred
    return required - user_profile  # True gaps
```

### 3. Temporal Trend Forecasting

```python
def forecast_demand(skill: str) -> dict:
    # Multi-source data fusion
    so_data = stack_exchange_api.get_tag_counts(skill)
    reddit_data = reddit_api.search_mentions(skill)
    
    # Prophet forecasting
    model = Prophet()
    model.fit(historical_data)
    forecast = model.predict(model.make_future_dataframe(periods=180))
    
    return {"trend": forecast['yhat'], "is_growing": True}
```

### 4. Modal Serverless Deployment

```python
app = modal.App("skillbridge")

@app.function(schedule=modal.Cron("0 2 * * *"))
async def daily_ai_surfer():
    return await run_update()

@app.function()
@modal.web_endpoint(method="POST")
async def analyze_resume(request: dict):
    result = await analyze_user(request['resume'], request['target_role'])
    return {"gaps": result['gaps'], "path": result['path']}
```

---

## 🎯 Competitive Advantages

| Feature | LinkedIn Skills | O*NET | CAPER | SkillBridge |
|---------|----------------|-------|-------|-------------|
| **Update Frequency** | Quarterly | Annual | Static | **Daily** |
| **Inference-Aware** | ❌ | ❌ | ❌ | **✅** |
| **Temporal Modeling** | ❌ | ❌ | ✅ | **✅ Advanced** |
| **Data Sources** | Single | Single | Single | **Multi (3)** |
| **Deployment** | Proprietary | Public | Research | **Production** |

---

## 📈 Example Results

**Advanced User Case Study:**
- **Input**: ML Engineer with PyTorch, TensorFlow, scikit-learn
- **Target**: AI Engineer
- **Baseline System**: 6 skill gaps (including redundant "Machine Learning", "Statistics")
- **SkillBridge**: 4 skill gaps (33% reduction) - correctly inferred foundational knowledge

---

## 🧪 Testing & Validation

Run comprehensive test suite:
```bash
python test_runner.py
```

**Test Coverage:**
- Knowledge graph quality validation (F1-score: 0.754)
- Recommendation engine accuracy (25-33% reduction verified)
- Temporal forecasting validation (100% success rate)
- System performance benchmarks (~30s response time)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Modal Labs** for serverless infrastructure
- **TiDB Cloud** for distributed database
- **AIML API** and **Nebius AI** for LLM access
- **VIT University** for academic support

---

## 📞 Contact

**Authors:**
- Mahalakshmi Balan - [mahalakshmi.b2022a@vitstudent.ac.in](mailto:mahalakshmi.b2022a@vitstudent.ac.in)
- Pratik A Shah - [pratik.ashah2022@vitstudent.ac.in](mailto:pratik.ashah2022@vitstudent.ac.in)

**Supervisor:**
- Dr. Yuvaraj Natarajan - [yuvaraj.n@vit.ac.in](mailto:yuvaraj.n@vit.ac.in)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

</div>
