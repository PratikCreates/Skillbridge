import streamlit as st
import requests
import time
import os
import pandas as pd
import graphviz
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# --- Helper Functions for API Interaction ---

@st.cache_data(ttl=3600)  # Cache roles for 1 hour
def load_roles_from_api(api_url: str) -> list[str]:
    """Fetches and caches the list of available roles from the backend."""
    try:
        response = requests.get(f"{api_url}/get_roles", timeout=20)
        response.raise_for_status()
        roles = response.json().get("roles", [])
        default_roles = ["Data Scientist", "Frontend Developer", "AI Engineer"]
        # Combine, remove duplicates, and sort for a clean list
        return sorted(list(set(roles + default_roles)))
    except requests.exceptions.RequestException as e:
        st.toast(f"Could not fetch live roles: {e}", icon="⚠️")
        return ["Data Scientist", "Frontend Developer", "AI Engineer", "Cloud Architect"]

@st.cache_data(ttl=3600)
def get_skill_graph_data(api_url: str) -> list:
    """Fetches the full skill graph from the backend for visualization."""
    try:
        response = requests.get(f"{api_url}/get_skill_graph", timeout=20)
        response.raise_for_status()
        return response.json().get("edges", [])
    except requests.exceptions.RequestException:
        return []

# --- Helper Functions for UI Rendering ---

def display_system_insights(start_time, end_time, result):
    """Displays system insights in the sidebar."""
    duration = end_time - start_time
    extracted_count = len(result.get("extracted_skills", []))
    gaps_count = len(result.get("learning_path", {}).get("path", []))
    with st.sidebar:
        st.markdown("---")
        st.header("System Insights")
        st.metric("Analysis Speedrun ⏱️", f"{duration:.2f}s")
        st.markdown(f"- **🧠 Skills Extracted:** {extracted_count}\n- **🎯 Gaps Identified:** {gaps_count}")
        st.caption("Powered by a serverless, autonomous AI engine.")

# --- Main Application ---

def main():
    load_dotenv()
    MODAL_API_URL = os.getenv("MODAL_WEB_URL")
    if not MODAL_API_URL:
        st.error("MODAL_WEB_URL environment variable is not set in your .env file.")
        st.stop()

    st.set_page_config(layout="wide", page_title="SkillBridge AI")
    
    # Add responsive CSS for better mobile experience
    st.markdown("""
    <style>
    /* Main container responsive adjustments */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Responsive video containers */
    .stVideo > div {
        max-width: 100% !important;
    }
    
    /* Better mobile sidebar */
    @media (max-width: 768px) {
        .css-1d391kg {
            width: 100% !important;
        }
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Responsive dataframe */
    .stDataFrame {
        width: 100%;
        overflow-x: auto;
    }
    
    /* Better button spacing */
    .stButton > button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    
    /* Responsive expander content */
    .streamlit-expanderContent {
        padding: 1rem;
    }
    
    /* Better tab content spacing */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables robustly
    st.session_state.setdefault('result', None)
    st.session_state.setdefault('completed_skills', set())
    st.session_state.setdefault('roles', None) # Start with None to trigger one-time load

    # --- Sidebar for User Inputs ---
    with st.sidebar:
        st.title("🚀 SkillBridge")
        st.header("1. Your Goal")
        
        # --- FIX: SAFE ROLE LOADING ---
        if st.session_state.roles is None:
            with st.spinner("Loading available roles..."):
                st.session_state.roles = load_roles_from_api(MODAL_API_URL)
            # Only rerun if we actually got roles to prevent infinite loop
            if st.session_state.roles and len(st.session_state.roles) > 0:
                st.rerun()

        target_role = st.selectbox("Target Career:", st.session_state.roles or ["Loading..."])

        st.header("2. Your Profile")
        uploaded_file = st.file_uploader("Upload Resume:", type=["pdf", "docx", "txt"])
        
        analyze_button = st.button("Analyze My Resume", disabled=(not uploaded_file), width="stretch", type="primary")

    # --- Main Content Area ---
    st.header("AI Career Platform")
    st.markdown("An autonomous, self-improving system for career trajectory analysis.")

    if analyze_button:
        st.session_state.result = None
        st.session_state.completed_skills = set()
        st.session_state.start_time = time.time()

        with st.spinner("Contacting AI engine... This can take a moment."):
            form_data = {"target_role": target_role}
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                start_response = requests.post(f"{MODAL_API_URL}/analyze_career", data=form_data, files=files, timeout=30)
                start_response.raise_for_status()
                call_id = start_response.json().get("call_id")

                with st.status("AI is processing your profile...", expanded=True) as status:
                    max_attempts = 60  # 5 minutes max
                    attempts = 0
                    while attempts < max_attempts:
                        time.sleep(5)
                        attempts += 1
                        try:
                            poll_response = requests.get(f"{MODAL_API_URL}/get_result", params={"call_id": call_id}, timeout=30)
                            poll_response.raise_for_status()
                            data = poll_response.json()
                            if data.get("status") != "running":
                                st.session_state.result = data
                                status.update(label="Analysis Complete!", state="complete", expanded=False)
                                break
                        except requests.exceptions.RequestException as e:
                            logger.error(f"Polling error: {e}")
                            if attempts >= 3:  # Fail after 3 consecutive errors
                                st.error("Connection lost during analysis. Please try again.")
                                break
                    else:
                        st.error("Analysis timed out. Please try again with a smaller resume or contact support.")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to communicate with the backend: {e}")

    # --- Display Results ---
    if st.session_state.result:
        result = st.session_state.result
        if st.session_state.start_time > 0:
            display_system_insights(st.session_state.start_time, time.time(), result)

        if "error" in result:
            st.error(f"Analysis Error: {result['error']}")
        else:
            st.success(f"**Analysis Complete!** Your profile has been successfully evaluated for the **{target_role}** role.")

            with st.expander("View All Extracted Skills"):
                st.info(", ".join(result.get("extracted_skills", [])))

            st.subheader(f"📊 Skill Analysis & Trend Forecast for: {target_role}")
            report = result.get("skill_analysis_report", {})
            if report and report.get("required_skills"):
                df = pd.DataFrame(report["required_skills"])
                df["Status"] = df["user_has_skill"].apply(lambda x: "✔️ Acquired" if x else "❌ Gap")
                df["growth_percentage"] = pd.to_numeric(df["growth_percentage"], errors='coerce').fillna(0)
                def get_trend_indicator(growth):
                    if growth > 10: return f"🔥 Trending ({growth:.1f}%)"
                    if growth > 0.1: return f"↗️ Growing ({growth:.1f}%)"  # Only show growing if > 0.1%
                    if growth < -5: return f"↘️ Declining ({growth:.1f}%)"
                    return "➡️ Stable"
                df["Trend Forecast"] = df["growth_percentage"].apply(get_trend_indicator)
                df["market_demand_score"] = pd.to_numeric(df["market_demand_score"], errors='coerce').fillna(0).astype(int)
                max_score = df["market_demand_score"].max() or 1
                st.dataframe(
                    df[["Status", "skill_name", "market_demand_score", "Trend Forecast"]],
                    column_config={
                        "skill_name": "Required Skill",
                        "market_demand_score": st.column_config.ProgressColumn("Current Market Demand", format="%d", min_value=0, max_value=int(max_score)),
                        "Trend Forecast": "6-Month Trend"
                    },
                    width="stretch", hide_index=True
                )

            st.subheader("🗺️ Your Personalized Learning Roadmap")
            learning_path = result.get("learning_path", {}).get("path", [])
            resources = result.get("learning_resources", [])
            
            # Check for skill gaps in the analysis report
            has_skill_gaps = False
            if report and report.get("required_skills"):
                has_skill_gaps = any(not skill.get("user_has_skill", True) for skill in report["required_skills"])
            
            # Show congratulations only if no learning path AND no skill gaps
            if not learning_path and not has_skill_gaps:
                st.balloons(); st.success("### 🎉 Congratulations! Your skills align with this role.")
            elif not learning_path and has_skill_gaps:
                st.warning("### ⚠️ Skill gaps identified, but no learning path was generated. Please try analyzing again or contact support.")
            elif has_skill_gaps and not resources:
                st.info("### 📚 Learning path identified, but resources are still being generated...")
            elif learning_path or (has_skill_gaps and resources):
                with st.expander("💡 Show Career Path Explanation Graph"):
                    with st.spinner("Generating explanation graph..."):
                        edges = get_skill_graph_data(MODAL_API_URL)
                        if edges:
                            g = graphviz.Digraph(graph_attr={'bgcolor': 'transparent'})
                            g.attr('node', shape='box', style='rounded,filled', fontname="Helvetica", fontsize="10", fontcolor="white", color="white")
                            g.attr('edge', color="white", fontcolor="white", arrowsize="0.7")
                            path_nodes = set(learning_path)
                            user_skills_lower = {s.lower().strip() for s in result.get("extracted_skills", [])}
                            # Build a subgraph of relevant nodes
                            relevant_nodes = set(path_nodes)
                            for prereq, skill in edges:
                                if skill in path_nodes: 
                                    relevant_nodes.add(prereq)
                                if prereq in path_nodes:
                                    relevant_nodes.add(skill)
                            
                            # Color nodes based on their role
                            for node in relevant_nodes:
                                node_lower = node.lower().strip()
                                if node in path_nodes: 
                                    g.node(node, fillcolor='#1E8449', color='#ABEBC6')  # Green: Learning target
                                elif node_lower in user_skills_lower: 
                                    g.node(node, fillcolor='#2E86C1', color='#AED6F1')  # Blue: User has skill
                                else: 
                                    g.node(node, fillcolor='#424949', color='#99A3A4')  # Grey: Prerequisites
                            for prereq, skill in edges:
                                if prereq in relevant_nodes and skill in relevant_nodes: g.edge(prereq, skill)
                            st.graphviz_chart(g)
                            st.caption("Green nodes are your learning path. Blue are skills you have. Grey are related prerequisites.")

                def on_checkbox_change(skill_name):
                    if skill_name in st.session_state.completed_skills: st.session_state.completed_skills.remove(skill_name)
                    else: st.session_state.completed_skills.add(skill_name)

                for i, step in enumerate(resources):
                    skill = step.get('skill')
                    if not skill: continue
                    is_completed = skill in st.session_state.completed_skills
                    st.checkbox(f"**Step {i+1}: Learn {skill}**", value=is_completed, key=f"skill_{skill}", on_change=on_checkbox_change, args=(skill,))
                    if not is_completed:
                        with st.expander("Show Learning Resources & Options"):
                            if i == 0:
                                if st.button(f"🔍 Find Deeper Prerequisites for {skill}", width="stretch"):
                                    with st.spinner(f"AI is finding foundational concepts for {skill}..."):
                                        res = requests.get(f"{MODAL_API_URL}/find_deeper_prereqs", params={"skill_name": skill}, timeout=20)
                                        if res.status_code == 200: st.info(f"**Foundational Concepts:** {', '.join(res.json().get('prerequisites', []))}")
                                        else: st.error("Could not fetch deeper prerequisites.")
                            
                            video_tab, resource_tab = st.tabs(["▶️ Video Tutorials", "📚 Repositories & Courses"])
                            with video_tab:
                                youtube_tutorials = step.get('youtube_tutorials', [])
                                if not youtube_tutorials: 
                                    st.info("No embeddable video tutorials found for this skill.")
                                else:
                                    # Create responsive video layout
                                    for idx, video in enumerate(youtube_tutorials):
                                        with st.container():
                                            # Use columns for better responsive layout
                                            col1, col2 = st.columns([2, 1])
                                            with col1:
                                                # Custom CSS for responsive video
                                                st.markdown("""
                                                <style>
                                                .video-container {
                                                    position: relative;
                                                    width: 100%;
                                                    height: 0;
                                                    padding-bottom: 56.25%; /* 16:9 aspect ratio */
                                                    margin-bottom: 1rem;
                                                }
                                                .video-container iframe {
                                                    position: absolute;
                                                    top: 0;
                                                    left: 0;
                                                    width: 100%;
                                                    height: 100%;
                                                    max-width: 560px;
                                                    max-height: 315px;
                                                }
                                                @media (max-width: 768px) {
                                                    .video-container {
                                                        padding-bottom: 75%; /* More square on mobile */
                                                    }
                                                }
                                                </style>
                                                """, unsafe_allow_html=True)
                                                
                                                # Extract video ID for responsive embed
                                                video_url = video['url']
                                                if 'youtube.com/watch?v=' in video_url:
                                                    video_id = video_url.split('watch?v=')[1].split('&')[0]
                                                    embed_html = f"""
                                                    <div class="video-container">
                                                        <iframe 
                                                            src="https://www.youtube.com/embed/{video_id}" 
                                                            frameborder="0" 
                                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                                            allowfullscreen>
                                                        </iframe>
                                                    </div>
                                                    """
                                                    st.markdown(embed_html, unsafe_allow_html=True)
                                                else:
                                                    # Fallback to st.video with width constraint
                                                    st.video(video_url, start_time=0)
                                            
                                            with col2:
                                                st.markdown("**Video Info:**")
                                                difficulty = video.get('difficulty', 'General')
                                                difficulty_emoji = {"Basic": "🟢", "Medium": "🟡", "Advanced": "🔴"}.get(difficulty, "⚪")
                                                st.caption(f"**{difficulty_emoji} {difficulty}:** {video['title'][:45]}{'...' if len(video['title']) > 45 else ''}")
                                                st.caption(f"📺 *{video['channel']}*")
                                                st.link_button("🔗 Open in YouTube", video_url, help="Open video in new tab")
                                        
                                        if idx < len(youtube_tutorials) - 1:
                                            st.divider()
                            with resource_tab:
                                st.link_button("Search for Courses on Coursera", step.get('coursera_search_link', 'https://coursera.org'), width="stretch")
                                
                                github_repos = step.get('github_repositories', [])
                                if not github_repos: 
                                    st.info("🔍 No specific repositories found. Try searching GitHub directly for hands-on projects.")
                                    # Provide helpful search suggestions
                                    search_suggestions = [
                                        f"{skill.replace(' ', '+')}+tutorial",
                                        f"{skill.replace(' ', '+')}+project+beginner",
                                        f"{skill.replace(' ', '+')}+example+implementation"
                                    ]
                                    st.markdown("**Try these GitHub searches:**")
                                    for suggestion in search_suggestions:
                                        search_url = f"https://github.com/search?q={suggestion}&type=repositories&s=stars&o=desc"
                                        st.link_button(f"🔍 {suggestion.replace('+', ' ')}", search_url)
                                else:
                                    st.markdown("**🛠️ Hands-on Projects & Tutorials:**")
                                    st.caption("💡 Look for repositories with clear README files, recent commits, and practical examples you can run locally.")
                                    for idx, repo in enumerate(github_repos):
                                        with st.container(border=True):
                                            # Header with repo name and stars
                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.markdown(f"**[{repo['name']}]({repo['url']})**")
                                            with col2:
                                                if repo['stars'] > 1000:
                                                    st.markdown(f"⭐ **{repo['stars']:,}**")
                                                else:
                                                    st.markdown(f"⭐ {repo['stars']}")
                                            
                                            # Description with better formatting
                                            description = repo.get('description', 'No description available.')
                                            if description and description != 'No description available.':
                                                # Smart truncation - keep it concise but meaningful
                                                if len(description) > 120:
                                                    # Find a good breaking point
                                                    truncated = description[:120]
                                                    last_space = truncated.rfind(' ')
                                                    if last_space > 80:
                                                        description = truncated[:last_space] + "..."
                                                    else:
                                                        description = truncated + "..."
                                                
                                                st.caption(f"📝 {description}")
                                            else:
                                                st.caption("📝 Repository focused on practical implementation")
                                            
                                            # Action buttons
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.link_button("🔗 View Code", repo['url'], help="Open repository on GitHub")
                                            with col2:
                                                # Create a direct search link for similar projects
                                                search_query = f"{skill.replace(' ', '+')}+tutorial+project"
                                                search_url = f"https://github.com/search?q={search_query}&type=repositories&s=stars&o=desc"
                                                st.link_button("🔍 Find Similar", search_url, help="Search for more projects like this")
                                        
                                        if idx < len(github_repos) - 1:
                                            st.markdown("---")
                
                total_skills = len(learning_path)
                progress = len(st.session_state.completed_skills) / total_skills if total_skills else 0
                st.progress(progress, text=f"{len(st.session_state.completed_skills)} / {total_skills} Skills Mastered")
                if progress == 1.0:
                    st.balloons(); st.success("### 🏆 Roadmap Complete! You've mastered all the required skills!")
            else:
                # Edge case: unexpected state
                st.info("### 🤔 Analysis complete, but unable to determine learning path status. Please try again.")

if __name__ == "__main__":
    main()