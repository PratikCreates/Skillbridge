import requests
import logging
import functools
import re
from urllib.parse import quote_plus

# BeautifulSoup is no longer needed as the scraper is removed.

from skillbridge.utils.config import (
    YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, 
    REDDIT_USER_AGENT, STACKEXCHANGE_API_KEY
)
from langchain_community.utilities.reddit_search import RedditSearchAPIWrapper
from langchain_community.tools.reddit_search.tool import RedditSearchSchema, RedditSearchRun

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubClient:
    """Client to search for repositories on GitHub without authentication."""
    
    # Skill-specific search strategies to avoid generic results
    SKILL_SEARCH_STRATEGIES = {
        "cloud computing": [
            "cloud+computing+tutorial+NOT+awesome",
            "aws+azure+gcp+tutorial",
            "cloud+infrastructure+terraform",
            "kubernetes+docker+cloud"
        ],
        "machine learning": [
            "machine+learning+tutorial+NOT+awesome",
            "ml+projects+python",
            "deep+learning+implementation",
            "scikit-learn+tensorflow+pytorch"
        ],
        "data science": [
            "data+science+projects+NOT+awesome",
            "data+analysis+python+jupyter",
            "pandas+numpy+matplotlib",
            "data+visualization+projects"
        ],
        "python": [
            "python+projects+NOT+awesome",
            "python+tutorial+beginner",
            "python+web+development",
            "python+automation+scripts"
        ],
        "javascript": [
            "javascript+projects+NOT+awesome",
            "js+tutorial+beginner",
            "react+vue+angular+projects",
            "nodejs+express+projects"
        ]
    }
    
    # Repositories to exclude (too generic)
    EXCLUDED_REPOS = {
        'sindresorhus/awesome',
        'ossu/computer-science', 
        'trimstray/the-book-of-secret-knowledge',
        'jwasham/coding-interview-university',
        'kamranahmedse/developer-roadmap',
        'public-apis/public-apis',
        'freeCodeCamp/freeCodeCamp'
    }
    
    @functools.lru_cache(maxsize=128)
    def search_repositories(self, skill_name: str, max_results: int = 3):
        logger.info(f"CACHE MISS: Calling GitHub API for '{skill_name}'")
        
        skill_lower = skill_name.lower()
        search_queries = self.SKILL_SEARCH_STRATEGIES.get(skill_lower, [
            f"{skill_name.replace(' ', '+')}+tutorial+NOT+awesome",
            f"{skill_name.replace(' ', '+')}+projects+NOT+list",
            f"{skill_name.replace(' ', '+')}+implementation+example"
        ])
        
        all_repos = []
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        # Try multiple search strategies
        for query in search_queries[:2]:  # Limit to 2 queries to avoid rate limits
            try:
                # Start with less restrictive filters, then add more if needed
                full_query = f"{query}+stars:>10"  # Much more lenient
                api_url = f"https://api.github.com/search/repositories?q={full_query}&sort=stars&order=desc&per_page=10"
                
                response = requests.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                repos = response.json().get('items', [])
                
                # Filter out excluded repositories and add to results
                for repo in repos:
                    repo_full_name = repo.get('full_name', '')
                    
                    # Check exclusion criteria
                    is_excluded = repo_full_name in self.EXCLUDED_REPOS
                    has_generic_terms = any(excluded in repo_full_name.lower() for excluded in ['awesome', 'list', 'collection'])
                    is_full = len(all_repos) >= max_results * 2
                    
                    # Calculate relevance score first to filter low-quality results
                    relevance_score = self._calculate_relevance_score(repo, skill_name)
                    
                    if not is_excluded and not has_generic_terms and not is_full and relevance_score > 0:
                        all_repos.append({
                            'name': repo.get('full_name'),
                            'url': repo.get('html_url'),
                            'stars': repo.get('stargazers_count', 0),
                            'description': repo.get('description', ''),
                            'language': repo.get('language', ''),
                            'updated_at': repo.get('updated_at', ''),
                            'relevance_score': relevance_score
                        })
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching GitHub data for query '{query}': {e}")
                continue
        
        # Sort by relevance score and return top results
        all_repos.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return clean results without internal scoring
        return [{
            'name': repo['name'],
            'url': repo['url'],
            'stars': repo['stars'],
            'description': repo['description']
        } for repo in all_repos[:max_results]]
    
    def _calculate_relevance_score(self, repo, skill_name):
        """Calculate relevance score based on multiple factors."""
        if not repo or not skill_name:
            return 0
            
        score = 0
        skill_words = skill_name.lower().split()
        
        # Safely handle potentially None values
        name = repo.get('full_name') or ''
        name_lower = name.lower() if name else ''
        
        description = repo.get('description') or ''
        description_lower = description.lower() if description else ''
        
        # Must have at least one skill word to be relevant
        has_skill_word = False
        for word in skill_words:
            if word in name_lower:
                score += 15  # Higher weight for name matches
                has_skill_word = True
            if word in description_lower:
                score += 8   # Good weight for description matches
                has_skill_word = True
        
        # If no skill words found, heavily penalize
        if not has_skill_word:
            score -= 50
        
        # Boost for tutorial/project keywords
        tutorial_keywords = ['tutorial', 'example', 'project', 'guide', 'learn', 'course', 'workshop', 'demo']
        for keyword in tutorial_keywords:
            if keyword in name_lower:
                score += 10
            elif keyword in description_lower:
                score += 5
        
        # Penalize irrelevant terms more heavily
        irrelevant_terms = ['torrent', 'movie', 'download', 'piracy', 'crack', 'hack', 'cheat']
        for term in irrelevant_terms:
            if term in name_lower or term in description_lower:
                score -= 100  # Heavy penalty
        
        # Penalize generic terms
        generic_terms = ['awesome', 'list', 'collection', 'resources', 'links']
        for term in generic_terms:
            if term in name_lower:
                score -= 30
        
        # Boost for recent activity (within 2 years)
        try:
            from datetime import datetime, timedelta
            updated_at = repo.get('updated_at', '')
            if updated_at:
                update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                if update_date > datetime.now().replace(tzinfo=update_date.tzinfo) - timedelta(days=730):
                    score += 8
        except:
            pass
        
        # Boost for programming languages that match the skill
        language = repo.get('language') or ''
        language = language.lower() if language else ''
        if language and any(lang in skill_name.lower() for lang in ['python', 'javascript', 'java', 'go', 'rust']):
            if language in skill_name.lower():
                score += 10
        
        # Normalize by stars (but don't let it dominate)
        stars = repo.get('stargazers_count', 0)
        star_bonus = min(stars / 500, 15)  # More generous star bonus
        
        return score + star_bonus

class CourseraClient:
    """Client to generate search links for Coursera."""
    def get_search_link(self, skill_name: str) -> str:
        return f"https://www.coursera.org/search?query={quote_plus(skill_name)}"

class YouTubeClient:
    def __init__(self):
        self.request_count = 0
        self.max_requests_per_hour = 100  # Conservative limit
    
    @functools.lru_cache(maxsize=128)
    def search_videos(self, skill_name: str, difficulty: str = "basic", max_results: int = 3):
        logger.info(f"CACHE MISS: Calling YouTube API for '{skill_name}' at {difficulty} level")
        
        # Difficulty-based search terms
        difficulty_terms = {
            "basic": ["tutorial for beginners", "introduction to", "getting started with"],
            "medium": ["intermediate tutorial", "practical guide", "hands-on"],
            "advanced": ["advanced tutorial", "deep dive", "masterclass"]
        }
        
        # Use appropriate search term based on difficulty
        search_term = difficulty_terms.get(difficulty, difficulty_terms["basic"])[0]
        search_query = f"{skill_name} {search_term}"
        
        # Step 1: Search for videos (get more results to filter best ones)
        search_results = max_results * 3  # Get 3x more to filter best ones
        api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={quote_plus(search_query)}&type=video&videoEmbeddable=true&key={YOUTUBE_API_KEY}&maxResults={search_results}"
        
        try:
            # Check API key exists
            if not YOUTUBE_API_KEY:
                logger.error("YouTube API key not configured")
                return []
            
            # Rate limiting check
            if self.request_count >= self.max_requests_per_hour:
                logger.warning("YouTube API rate limit reached")
                return []
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            self.request_count += 1
            videos = response.json().get('items', [])
            
            if not videos:
                return []
            
            # Step 2: Get detailed statistics for engagement metrics
            video_ids = ",".join([video['id']['videoId'] for video in videos])
            stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id={video_ids}&key={YOUTUBE_API_KEY}"
            
            stats_response = requests.get(stats_url, timeout=10)
            stats_response.raise_for_status()
            self.request_count += 1
            stats_data = stats_response.json().get('items', [])
            
            # Create a mapping of video_id to stats
            stats_map = {item['id']: item for item in stats_data}
            
            # Step 3: Calculate quality scores and sort
            video_scores = []
            for video in videos:
                video_id = video['id']['videoId']
                stats = stats_map.get(video_id, {}).get('statistics', {})
                
                # Calculate engagement score
                likes = int(stats.get('likeCount', 0))
                views = int(stats.get('viewCount', 1))  # Avoid division by zero
                comments = int(stats.get('commentCount', 0))
                
                # Quality score: likes per 1000 views + comments per 1000 views (weighted)
                like_ratio = (likes / views) * 1000 if views > 0 else 0
                comment_ratio = (comments / views) * 1000 if views > 0 else 0
                engagement_score = like_ratio + (comment_ratio * 0.5)  # Comments weighted less than likes
                
                # Bonus for higher view counts (popularity)
                view_bonus = min(views / 10000, 10)  # Cap bonus at 10 points
                
                total_score = engagement_score + view_bonus
                
                video_info = {
                    'title': video['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'channel': video['snippet']['channelTitle'],
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'engagement_score': round(total_score, 2)
                }
                
                video_scores.append(video_info)
            
            # Step 4: Sort by engagement score (highest first) and return top results
            video_scores.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            # Return top videos without exposing internal metrics
            return [{
                'title': video['title'],
                'url': video['url'],
                'channel': video['channel']
            } for video in video_scores[:max_results]]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching YouTube data for '{skill_name}': {e}")
            return []

class StackOverflowClient:
    """An authenticated client to get trend data from Stack Overflow."""
    
    # Skill name to StackOverflow tag mapping for better accuracy
    SKILL_TAG_MAPPING = {
        "cloud ai platforms": "google-cloud-platform",
        "cloud ai": "artificial-intelligence",
        "machine learning": "machine-learning",
        "deep learning": "deep-learning",
        "natural language processing": "nlp",
        "computer vision": "computer-vision",
        "mlops": "devops",
        "data science": "data-science",
        "python": "python",
        "tensorflow": "tensorflow",
        "pytorch": "pytorch",
        "aws": "amazon-web-services",
        "azure": "azure",
        "gcp": "google-cloud-platform",
        "kubernetes": "kubernetes",
        "docker": "docker"
    }

    @functools.lru_cache(maxsize=256)
    def get_skill_trend_score(self, skill_name: str) -> int:
        logger.info(f"CACHE MISS: Calling Stack Overflow API for tag '{skill_name}'")
        
        # Use mapping if available, otherwise convert to tag format
        skill_lower = skill_name.lower()
        if skill_lower in self.SKILL_TAG_MAPPING:
            tag = self.SKILL_TAG_MAPPING[skill_lower]
            logger.info(f"Using mapped tag '{tag}' for skill '{skill_name}'")
        else:
            tag = skill_lower.replace(" ", "-")
            
        params = {"site": "stackoverflow", "key": STACKEXCHANGE_API_KEY}
        api_url = f"https://api.stackexchange.com/2.3/tags/{quote_plus(tag)}/info"
        try:
            if not params["key"]:
                logger.warning("STACKEXCHANGE_API_KEY not found. Call may be rate-limited.")
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get("items", [])
            count = items[0].get("count", 0) if items else 0
            
            # If we get 0 and used the original tag format, try some fallback mappings
            if count == 0 and skill_lower not in self.SKILL_TAG_MAPPING:
                fallback_tags = []
                if "ai" in skill_lower or "artificial intelligence" in skill_lower:
                    fallback_tags.append("artificial-intelligence")
                if "cloud" in skill_lower:
                    fallback_tags.append("google-cloud-platform")
                if "platform" in skill_lower:
                    fallback_tags.append("platform")
                    
                for fallback_tag in fallback_tags:
                    try:
                        fallback_url = f"https://api.stackexchange.com/2.3/tags/{quote_plus(fallback_tag)}/info"
                        fallback_response = requests.get(fallback_url, params=params, timeout=10)
                        fallback_response.raise_for_status()
                        fallback_items = fallback_response.json().get("items", [])
                        fallback_count = fallback_items[0].get("count", 0) if fallback_items else 0
                        if fallback_count > 0:
                            logger.info(f"Using fallback tag '{fallback_tag}' with count {fallback_count} for skill '{skill_name}'")
                            return fallback_count
                    except:
                        continue
                        
            return count
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Stack Overflow data for tag '{tag}': {e}")
            return 0

class RedditClient:
    """An authenticated client for getting discussion data from Reddit using LangChain."""

    def __init__(self):
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT:
            self.api_wrapper = RedditSearchAPIWrapper(
                reddit_client_id=REDDIT_CLIENT_ID,
                reddit_client_secret=REDDIT_CLIENT_SECRET,
                reddit_user_agent=REDDIT_USER_AGENT,
            )
            self.search_tool = RedditSearchRun(api_wrapper=self.api_wrapper)
        else:
            self.search_tool = None
            logger.warning("Reddit API credentials not found. RedditClient will be disabled.")
    
    @functools.lru_cache(maxsize=256)
    def get_skill_trend_score(self, skill_name: str, subreddit: str = "MachineLearning") -> int:
        """Get trend score for a skill from Reddit discussions."""
        if not self.search_tool:
            logger.warning("Reddit client not initialized. Returning 0.")
            return 0
        try:
            search_params = RedditSearchSchema(
                query=skill_name, subreddit=subreddit, limit="10",
                sort="relevance", time_filter="month"
            )
            result_str = self.search_tool.run(tool_input=search_params.model_dump())
            scores = re.findall(r"Score: (\d+)", result_str)
            return sum(int(score) for score in scores)
        except Exception as e:
            logger.error(f"Error fetching Reddit data for '{skill_name}': {e}")
            return 0

# --- The JobScraperClient class has been removed. ---
# It is now replaced by the more robust `researcher_client.py`.