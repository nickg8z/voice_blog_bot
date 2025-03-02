import requests
import jwt
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


def publish_to_ghost_blog(title, content, api_url, admin_api_key, tags=None):
    """
    Publish a post to Ghost blog using the direct JWT approach from Ghost docs.

    Args:
        title (str): Post title
        content (str): Post content in markdown format
        api_url (str): Ghost blog URL
        admin_api_key (str): Admin API key in format 'id:secret'
        tags (list): Optional list of tag names

    Returns:
        tuple: (success, result)
    """
    try:
        # Split the key into ID and SECRET
        id_val, secret = admin_api_key.split(":")

        # Prepare header and payload
        iat = int(datetime.now().timestamp())

        header = {"alg": "HS256", "typ": "JWT", "kid": id_val}
        payload = {"iat": iat, "exp": iat + 5 * 60, "aud": "/admin/"}

        # Create the token
        token = jwt.encode(
            payload, bytes.fromhex(secret), algorithm="HS256", headers=header
        )

        # Convert token to string if it's bytes (depends on PyJWT version)
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        # Prepare the API URL
        api_url = api_url.rstrip("/")
        url = f"{api_url}/ghost/api/admin/posts/"

        # Prepare headers
        headers = {"Authorization": f"Ghost {token}"}

        # Prepare post data with mobiledoc format (required by your Ghost version)
        # Create a proper mobiledoc structure with the markdown content
        mobiledoc = {
            "version": "0.3.1",
            "markups": [],
            "atoms": [],
            "cards": [["markdown", {"markdown": content}]],
            "sections": [[10, 0]],
        }

        # Use only mobiledoc format since it worked in testing
        post_data = {
            "posts": [
                {
                    "title": title,
                    "mobiledoc": json.dumps(
                        mobiledoc
                    ),  # Mobiledoc is the format that worked in testing
                    "status": "published",
                    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
            ]
        }

        # Add tags if provided
        if tags:
            post_data["posts"][0]["tags"] = [{"name": tag} for tag in tags]

        # Add tags if provided
        if tags:
            post_data["posts"][0]["tags"] = [{"name": tag} for tag in tags]

        # Make the request
        response = requests.post(url, json=post_data, headers=headers)

        # Check if successful
        if response.status_code in (200, 201):
            # Process response
            result = response.json()
            post = result.get("posts", [{}])[0]
            post_id = post.get("id")
            post_url = post.get("url")

            if not post_url:
                # Try to construct URL
                post_slug = post.get("slug")
                if post_slug:
                    post_url = f"{api_url}/{post_slug}"
                else:
                    post_url = f"Post published with ID: {post_id}"

            logger.info(f"Post published successfully: {post_url}")
            return True, post_url
        else:
            error_msg = (
                f"Failed to publish post: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            return False, error_msg

    except Exception as e:
        error_msg = f"Error publishing to Ghost: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


if __name__ == "__main__":
    # Test with environment variables
    api_url = os.getenv("BLOG_API_URL")
    admin_api_key = os.getenv("BLOG_API_KEY")

    if api_url and admin_api_key:
        success, result = publish_to_ghost_blog(
            "Test Post",
            "This is a test post from simple_ghost.py",
            api_url,
            admin_api_key,
            ["Test"],
        )
        print(f"Success: {success}")
        print(f"Result: {result}")
    else:
        print("Please set BLOG_API_URL and BLOG_API_KEY environment variables")
