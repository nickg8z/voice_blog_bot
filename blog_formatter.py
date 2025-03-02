import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BLOG_API_URL = os.getenv("BLOG_API_URL")
BLOG_API_KEY = os.getenv("BLOG_API_KEY")
BLOG_PLATFORM = os.getenv("BLOG_PLATFORM", "").lower()

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def generate_blog_post(transcriptions):
    """Generate a blog post from transcriptions using OpenRouter."""
    if not transcriptions:
        return "No content to generate a blog post."

    # Combine all transcriptions
    all_text = "\n\n".join(transcriptions)

    # Create the prompt for the LLM
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
I have recorded the following voice notes throughout the day on {today}. 
Please format them into a coherent, well-structured blog post. 
Organize related thoughts, correct any grammar or transcription errors, 
and make it flow naturally while preserving my original thoughts and insights.

Here are the notes:

{all_text}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://voiceblogbot.example.com",  # Optional but recommended
        "X-Title": "Voice Blog Bot",  # Optional but recommended
    }

    payload = {
        "model": "anthropic/claude-3.7-sonnet",  # Updated to use Claude 3.7 Sonnet
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_API_URL, headers=headers, json=payload
            )

            if response.status_code != 200:
                logger.error(
                    f"OpenRouter API error: {response.status_code}, {response.text}"
                )
                return f"Error generating blog post: {response.text}"

            result = response.json()
            blog_content = result["choices"][0]["message"]["content"]

            # Save the blog post locally as backup
            save_path = f"blog_posts/{today}.md"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(blog_content)

            return blog_content

    except Exception as e:
        logger.error(f"Error generating blog post: {str(e)}")
        return f"Error generating blog post: {str(e)}"


async def publish_to_ghost(blog_content, date_str):
    """Publish the blog post to Ghost using the simple JWT approach."""
    if not BLOG_API_URL or not BLOG_API_KEY:
        logger.warning("Ghost API details not configured. Saving locally only.")
        return False, "Ghost API details not configured"

    try:
        # Format the blog post title based on the date
        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        title = f"Daily Reflections - {formatted_date}"

        # Save the blog post locally regardless
        local_path = f"blog_posts/{date_str}.md"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(blog_content)
        logger.info(f"Blog post saved locally to {local_path}")

        # Import our simple Ghost publishing function
        from simple_ghost import publish_to_ghost_blog

        # Create the post
        success, result = publish_to_ghost_blog(
            title=title,
            content=blog_content,
            api_url=BLOG_API_URL,
            admin_api_key=BLOG_API_KEY,
            tags=["Daily Reflections", "Voice Notes"],
        )

        if success:
            logger.info(f"Successfully published to Ghost: {result}")

            # Save the URL if available
            if isinstance(result, str) and result.startswith("http"):
                with open(f"blog_posts/{date_str}_url.txt", "w") as f:
                    f.write(result)

            return True, result
        else:
            logger.error(f"Failed to publish to Ghost: {result}")
            return False, result

    except Exception as e:
        error_msg = f"Error publishing to Ghost: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


async def publish_to_wordpress(blog_content, date_str):
    """Publish the blog post to WordPress via REST API."""
    if not BLOG_API_URL or not BLOG_API_KEY:
        logger.warning("WordPress API details not configured. Saving locally only.")
        return False, "WordPress API details not configured"

    try:
        # Format the blog post title based on the date
        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        title = f"Daily Reflections - {formatted_date}"

        # Prepare the payload for WordPress API
        payload = {
            "title": title,
            "content": blog_content,
            "status": "publish",  # or "draft" if you want to review before publishing
            "date": date_str,
            "format": "standard",
        }

        headers = {
            "Authorization": f"Bearer {BLOG_API_KEY}",
            "Content-Type": "application/json",
        }

        # WordPress REST API endpoint for posts
        api_endpoint = f"{BLOG_API_URL}/wp-json/wp/v2/posts"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_endpoint, headers=headers, json=payload)

            if response.status_code in (200, 201):
                post_data = response.json()
                post_id = post_data.get("id")
                post_url = post_data.get("link")
                logger.info(
                    f"Blog post published successfully to WordPress: {post_url}"
                )

                # Save the post URL for reference
                with open(f"blog_posts/{date_str}_url.txt", "w") as f:
                    f.write(post_url)

                return True, post_url
            else:
                logger.error(
                    f"Failed to publish to WordPress: {response.status_code}, {response.text}"
                )
                return (
                    False,
                    f"Failed to publish to WordPress: {response.status_code} - {response.text}",
                )

    except Exception as e:
        logger.error(f"Error publishing to WordPress: {str(e)}")
        return False, f"Error publishing to WordPress: {str(e)}"


async def publish_to_medium(blog_content, date_str):
    """Publish the blog post to Medium via their API."""
    if not BLOG_API_KEY:  # Medium only needs the API key
        logger.warning("Medium API key not configured. Saving locally only.")
        return False, "Medium API key not configured"

    try:
        # Format the blog post title based on the date
        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        title = f"Daily Reflections - {formatted_date}"

        # Prepare the payload for Medium API
        payload = {
            "title": title,
            "contentFormat": "markdown",  # Medium supports markdown
            "content": blog_content,
            "publishStatus": "public",  # or "draft" if you want to review
            "tags": ["daily-reflections", "voice-notes"],
        }

        headers = {
            "Authorization": f"Bearer {BLOG_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Medium API endpoint (first get user ID)
        user_endpoint = "https://api.medium.com/v1/me"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # First get the user ID
            user_response = await client.get(user_endpoint, headers=headers)

            if user_response.status_code != 200:
                logger.error(
                    f"Failed to get Medium user ID: {user_response.status_code}, {user_response.text}"
                )
                return (
                    False,
                    f"Failed to get Medium user ID: {user_response.status_code} - {user_response.text}",
                )

            user_data = user_response.json()
            user_id = user_data.get("data", {}).get("id")

            if not user_id:
                logger.error("Could not retrieve Medium user ID")
                return False, "Could not retrieve Medium user ID"

            # Now post to the user's Medium account
            post_endpoint = f"https://api.medium.com/v1/users/{user_id}/posts"

            post_response = await client.post(
                post_endpoint, headers=headers, json=payload
            )

            if post_response.status_code in (200, 201):
                post_data = post_response.json()
                post = post_data.get("data", {})
                post_id = post.get("id")
                post_url = post.get("url")

                logger.info(f"Blog post published successfully to Medium: {post_url}")

                # Save the post URL for reference
                with open(f"blog_posts/{date_str}_url.txt", "w") as f:
                    f.write(post_url)

                return True, post_url
            else:
                logger.error(
                    f"Failed to publish to Medium: {post_response.status_code}, {post_response.text}"
                )
                return (
                    False,
                    f"Failed to publish to Medium: {post_response.status_code} - {post_response.text}",
                )

    except Exception as e:
        logger.error(f"Error publishing to Medium: {str(e)}")
        return False, f"Error publishing to Medium: {str(e)}"


async def publish_to_blog(blog_content, date_str):
    """Publish the blog post to your blog."""
    # Save the blog post locally as a backup regardless of publishing success
    local_path = f"blog_posts/{date_str}.md"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(blog_content)
    logger.info(f"Blog post saved locally to {local_path}")

    # Choose the appropriate publishing method based on platform
    if BLOG_PLATFORM == "wordpress":
        logger.info("Using WordPress publishing method")
        try:
            return await publish_to_wordpress(blog_content, date_str)
        except Exception as e:
            error_msg = f"WordPress publishing error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    elif BLOG_PLATFORM == "ghost":
        logger.info("Using Ghost publishing method")
        try:
            return await publish_to_ghost(blog_content, date_str)
        except Exception as e:
            error_msg = f"Ghost publishing error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    elif BLOG_PLATFORM == "medium":
        logger.info("Using Medium publishing method")
        try:
            return await publish_to_medium(blog_content, date_str)
        except Exception as e:
            error_msg = f"Medium publishing error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    else:
        msg = f"Blog platform '{BLOG_PLATFORM}' not supported or not specified. Saving locally only."
        logger.warning(msg)
        return False, msg
