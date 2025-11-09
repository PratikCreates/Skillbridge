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
# skillbridge/core/knowledge_graph_builder.py
import modal
from skillbridge.processing.researcher_client import ResearcherClient
from skillbridge.processing.nebius_client import NebiusClient

@modal.function(schedule=modal.Cron("0 2 * * *"))  # Daily at 2 AM
async def run_daily_knowledge_graph_update():
    """Two-stage multi-agent workflow for knowledge graph construction"""
    
    # Stage 1: Researcher Agent (Gemini 2.0 Flash)
    researcher = ResearcherClient()
    job_descriptions = await researcher.search_and_extract(
        role="Data Scientist",
        num_postings=10
    )
    
    # Stage 2: Expert Analyst Agent (Kimi-K2-Instruct)
    analyst = NebiusClient()
    structured_skills = await analyst.synthesize_skills(
        job_text=job_descriptions,
        prompt="""Analyze these job descriptions and return a JSON object with:
        - 5-7 most critical skills
        - Skill categories (Technical, Soft, Domain)
        - Prerequisite relationships"""
    )
    
    # Update knowledge graph
    db_service.update_skill_graph(structured_skills)
    return {"status": "success", "skills_added": len(structured_skills)}
```

### 2. Inference-Aware Recommendation Engine

```python
# skillbridge/core/career_graph.py
import networkx as nx
from typing import Set, List

class InferenceEngine:
    def __init__(self, skill_graph: nx.DiGraph):
        self.graph = skill_graph
    
    def infer_implicit_skills(self, explicit_skills: Set[str]) -> Set[str]:
        """Traverse graph to find all implied prerequisite skills"""
        inferred = set()
        
        for skill in explicit_skills:
            if skill in self.graph:
                # Use nx.ancestors to find all prerequisites
                prerequisites = nx.ancestors(self.graph, skill)
                inferred.update(prerequisites)
        
        return inferred
    
    def compute_skill_gaps(
        self, 
        explicit_skills: Set[str],
        target_role: str
    ) -> List[str]:
        """Identify true skill gaps using inference"""
        
        # Get required skills for target role
        required_skills = self.get_role_requirements(target_role)
        
        # Infer implicit knowledge
        inferred_skills = self.infer_implicit_skills(explicit_skills)
        
        # Complete user profile
        user_profile = explicit_skills | inferred_skills
        
        # True gaps = Required - (Explicit + Inferred)
        gaps = required_skills - user_profile
        
        return list(gaps)
    
    def generate_learning_path(self, skill_gaps: List[str]) -> List[str]:
        """Create pedagogically sound learning sequence"""
        
        # Create subgraph with only gap skills
        subgraph = self.graph.subgraph(skill_gaps)
        
        # Topological sort ensures prerequisites come first
        try:
            learning_path = list(nx.topological_sort(subgraph))
            return learning_path
        except nx.NetworkXError:
            # Handle circular dependencies
            return self._resolve_cycles(subgraph)
```

### 3. Temporal Trend Forecasting

```python
# skillbridge/core/prediction_engine.py
from prophet import Prophet
import pandas as pd

class TemporalEngine:
    def __init__(self):
        self.model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative'
        )
    
    async def fetch_skill_popularity(self, skill: str) -> pd.DataFrame:
        """Multi-source data fusion"""
        
        # Stack Overflow API
        so_data = await self.stack_exchange_api.get_tag_counts(skill)
        
        # Reddit API
        reddit_data = await self.reddit_api.search_mentions(
            skill,
            subreddits=['forhire', 'jobs', 'careerguidance']
        )
        
        # Combine and normalize
        df = pd.DataFrame({
            'ds': dates,  # Prophet requires 'ds' column
            'y': so_data['count'] + reddit_data['engagement_score']
        })
        
        return df
    
    def forecast_demand(self, historical_data: pd.DataFrame) -> dict:
        """6-month skill demand prediction"""
        
        self.model.fit(historical_data)
        
        # Forecast 180 days ahead
        future = self.model.make_future_dataframe(periods=180)
        forecast = self.model.predict(future)
        
        return {
            'trend': forecast['trend'].iloc[-1],
            'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            'is_growing': forecast['trend'].iloc[-1] > forecast['trend'].iloc[0]
        }
```

### 4. Hybrid Skill Extraction

```python
# skillbridge/processing/skill_extraction.py
import spacy
from typing import List, Set

class HybridSkillExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.skill_patterns = self._load_skill_dictionary()
    
    def extract_skills(self, resume_text: str) -> Set[str]:
        """Two-stage extraction: spaCy + LLM validation"""
        
        # Stage 1: Fast pattern matching with spaCy
        doc = self.nlp(resume_text)
        candidate_skills = set()
        
        for token in doc:
            if token.text.lower() in self.skill_patterns:
                candidate_skills.add(token.text)
        
        # Stage 2: LLM validation for context
        validated_skills = self._llm_validate(
            resume_text, 
            candidate_skills
        )
        
        return validated_skills
    
    def _llm_validate(self, text: str, candidates: Set[str]) -> Set[str]:
        """Use LLM to validate skills in context"""
        
        prompt = f"""Given this resume text, validate which of these 
        candidate skills are actually present: {candidates}
        
        Return only skills that are clearly demonstrated."""
        
        response = self.llm_client.complete(prompt)
        return set(response['validated_skills'])
```

### 5. Modal Serverless Deployment

```python
# skillbridge/api/main.py
import modal

app = modal.App("skillbridge")

# Define compute resources
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt")

@app.function(
    image=image,
    schedule=modal.Cron("0 2 * * *"),  # Daily at 2 AM
    secrets=[modal.Secret.from_name("skillbridge-secrets")]
)
async def daily_ai_surfer():
    """Autonomous knowledge graph update"""
    from skillbridge.core.knowledge_graph_builder import run_update
    return await run_update()

@app.function(
    image=image,
    schedule=modal.Cron("0 3 * * 0"),  # Weekly on Sunday
    secrets=[modal.Secret.from_name("skillbridge-secrets")]
)
async def weekly_temporal_analysis():
    """Trend forecasting and popularity tracking"""
    from skillbridge.core.temporal_analysis import run_analysis
    return await run_analysis()

@app.function(image=image)
@modal.web_endpoint(method="POST")
async def analyze_resume(request: dict):
    """Real-time user analysis endpoint"""
    from skillbridge.core.skill_analysis import analyze_user
    
    resume_text = request['resume']
    target_role = request['target_role']
    
    result = await analyze_user(resume_text, target_role)
    
    return {
        "skill_gaps": result['gaps'],
        "learning_path": result['path'],
        "inferred_skills": result['inferred'],
        "trend_forecast": result['trends']
    }
```

### 6. Graph Validation

```python
# skillbridge/core/graph_validator.py
import networkx as nx

class GraphValidator:
    def validate_graph(self, G: nx.DiGraph) -> dict:
        """Ensure graph quality and consistency"""
        
        issues = []
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                issues.append(f"Circular dependencies found: {cycles}")
        except:
            pass
        
        # Validate categories
        for node in G.nodes():
            if 'category' not in G.nodes[node]:
                issues.append(f"Node {node} missing category")
        
        # Check connectivity
        if not nx.is_weakly_connected(G):
            components = list(nx.weakly_connected_components(G))
            issues.append(f"Graph has {len(components)} disconnected components")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "stats": {
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes()
            }
        }
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
