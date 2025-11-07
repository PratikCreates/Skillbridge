import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from skillbridge.processing.external_apis import GitHubClient, CourseraClient, YouTubeClient

logger = logging.getLogger(__name__)

class ResourceMatcher:
    def __init__(self):
        """Initializes API clients and the thread pool for parallel execution."""
        self.github_client = GitHubClient()
        self.coursera_client = CourseraClient()
        self.youtube_client = YouTubeClient()
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _fetch_for_single_skill(self, skill_details: Dict) -> Dict:
        """Fetches all resources for a single skill."""
        skill_name = skill_details.get("name", "Unknown")
        ai_keywords = skill_details.get("keywords", [])
        search_keywords = ai_keywords + [skill_name] # Add the skill name itself as the ultimate fallback
        
        github_repos = []
        for keyword in search_keywords:
            clean_keyword = keyword.replace("Skill:", "").strip()
            # The query is now simpler and more effective
            query = f'"{clean_keyword}" tutorial OR example in:readme,description stars:>100'
            github_repos = self.github_client.search_repositories(query)
            if github_repos:
                logger.info(f"Found GitHub repos for '{skill_name}' using query '{query}'.")
                break
        
        # Get YouTube videos for different difficulty levels
        youtube_videos = []
        difficulties = ["basic", "medium", "advanced"]
        
        for difficulty in difficulties:
            for keyword in search_keywords:
                clean_keyword = keyword.replace("Skill:", "").strip()
                videos = self.youtube_client.search_videos(clean_keyword, difficulty=difficulty, max_results=1)
                if videos:
                    # Add difficulty label to video info
                    for video in videos:
                        video['difficulty'] = difficulty.title()
                    youtube_videos.extend(videos)
                    logger.info(f"Found {len(videos)} {difficulty} YouTube videos for '{skill_name}'.")
                    break
            if len(youtube_videos) >= 3:  # Stop when we have enough videos
                break

        coursera_link = self.coursera_client.get_search_link(skill_name)
        return {
            "skill": skill_name,
            "github_repositories": github_repos,
            "coursera_search_link": coursera_link,
            "youtube_tutorials": youtube_videos,
        }

    def get_resources_for_path(self, skill_details_list: List[Dict]) -> List[Dict]:
        """Fetches resources for an entire learning path IN PARALLEL."""
        if not skill_details_list:
            return []
        
        logger.info(f"Starting parallel resource matching for {len(skill_details_list)} skills...")
        results = list(self.executor.map(self._fetch_for_single_skill, skill_details_list))
        logger.info("Parallel resource matching complete.")
        
        skill_order = [s.get("name") for s in skill_details_list]
        # Filter out potential failed results before sorting
        valid_results = [r for r in results if r.get('skill') in skill_order]
        sorted_results = sorted(valid_results, key=lambda x: skill_order.index(x['skill']))
        
        return sorted_results