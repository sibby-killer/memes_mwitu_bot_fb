import requests
import config

def upload_photo(file_url_or_path: str, is_local: bool = True) -> str:
    """
    Uploads a single photo to the Facebook page as 'unpublished' to get a Media ID.
    Returns the media_id (str) on success, or None on failure.
    """
    url = f"https://graph.facebook.com/v19.0/{config.FACEBOOK_PAGE_ID}/photos"
    
    # We upload photos but keep them hidden initially (published=false)
    payload = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        "published": "false"
    }

    try:
        if is_local:
            with open(file_url_or_path, 'rb') as f:
                files = {'source': f}
                response = requests.post(url, data=payload, files=files)
        else:
            payload['url'] = file_url_or_path
            response = requests.post(url, data=payload)
            
        result = response.json()
        
        if 'id' in result:
            return result['id']
        else:
            msg = result.get('error', {}).get('message', str(result))
            raise Exception(f"Facebook API Error: {msg}")
    except Exception as e:
        raise Exception(f"Upload photo failed: {str(e)}")

def publish_carousel(media_ids: list, message: str) -> str:
    """
    Publishes a post (carousel/album) using the attached media_ids and message.
    Returns the Post ID on success, or None on failure.
    """
    url = f"https://graph.facebook.com/v19.0/{config.FACEBOOK_PAGE_ID}/feed"
    
    payload = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        "message": message
    }
    
    # Attach each uploaded photo to this new multi-photo post structure
    for idx, mid in enumerate(media_ids):
        payload[f'attached_media[{idx}]'] = f'{{"media_fbid":"{mid}"}}'
        
    try:
        response = requests.post(url, data=payload)
        result = response.json()
        
        if 'id' in result:
            return result['id']
        else:
            msg = result.get('error', {}).get('message', str(result))
            raise Exception(f"Facebook API Error: {msg}")
    except Exception as e:
        raise Exception(f"Publish carousel failed: {str(e)}")

def publish_text_only(message: str) -> str:
    """
    Posts a raw text status to the Facebook Page.
    Returns the Post ID on success, or None on failure.
    """
    url = f"https://graph.facebook.com/v19.0/{config.FACEBOOK_PAGE_ID}/feed"
    
    payload = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        "message": message
    }
    
    try:
        response = requests.post(url, data=payload)
        result = response.json()
        if 'id' in result:
            return result['id']
        else:
            msg = result.get('error', {}).get('message', str(result))
            raise Exception(f"Facebook API Error: {msg}")
    except Exception as e:
        raise Exception(f"Publish text failed: {str(e)}")

def upload_video(file_path: str, message: str) -> str:
    """
    Uploads a video directly to the Facebook Page with the final caption.
    Returns the Post ID (video ID) on success, or None on failure.
    """
    url = f"https://graph.facebook.com/v19.0/{config.FACEBOOK_PAGE_ID}/videos"
    
    payload = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        "description": message
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'source': f}
            response = requests.post(url, data=payload, files=files)
            
        result = response.json()
        if 'id' in result:
            return result['id']
        else:
            msg = result.get('error', {}).get('message', str(result))
            raise Exception(f"Facebook API Error: {msg}")
    except Exception as e:
        raise Exception(f"Upload video failed: {str(e)}")

def post_comment(post_id: str, comment_text: str) -> bool:
    """
    Posts a comment to an existing Post. Used for dropping the CTA.
    Returns True on success, False otherwise.
    """
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    
    payload = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        "message": comment_text
    }
    
    try:
        response = requests.post(url, data=payload)
        result = response.json()
        
        if 'id' in result:
            return True
        else:
            print(f"Failed to post comment on {post_id}: {result}")
            return False
            
    except Exception as e:
        print(f"Exception posting comment: {e}")
        return False
