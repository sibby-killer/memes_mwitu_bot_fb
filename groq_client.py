from groq import Groq
import config

# Initialize Groq Client
# Ensure API key is present
if config.GROQ_API_KEY:
    client = Groq(api_key=config.GROQ_API_KEY)
else:
    client = None

def enhance_vibe(original_caption: str) -> dict:
    """
    Takes an original caption and uses Groq to generate:
    1. 5 trending, unique hashtags.
    2. A funny, foolish, unique CTA to be used as a comment.
    
    Returns a dictionary containing the strictly formatted hashtags and the CTA comment.
    """
    
    # We use a fast and reliable LLaMA model
    model = "llama3-8b-8192" 
    
    # Strict System Prompt
    system_prompt = """
    You are an expert social media manager for a meme page named "Meme Mwitu".
    Your entire objective is to output TWO specific items based on the user's caption.
    
    ITEM 1: 5 trending, highly relevant Facebook hashtags for the meme.
    ITEM 2: A short, funny, slightly foolish, unique Call-To-Action (CTA) asking people to follow/like the page.
    
    CRITICAL INSTRUCTION: You MUST format your response EXACTLY like this:
    HASHTAGS: #tag1 #tag2 #tag3 #tag4 #tag5
    CTA: [Your funny unique comment here]
    
    DO NOT output ANY other conversational text. Do not rewrite the caption. 
    Just exact hashtags and the CTA under it.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"The caption is: '{original_caption}'. Generate the hashtags and CTA."
                }
            ],
            model=model,
            temperature=0.8, # Slightly high for creativity on the CTA
        )
        
        output = response.choices[0].message.content.strip()
        
        # Parse output safely
        hashtags = ""
        cta = "Lol 😂 Follow the page for more Memes Mwitu!" # Fallback CTA
        
        for line in output.split('\n'):
            if line.startswith('HASHTAGS:'):
                hashtags = line.replace('HASHTAGS:', '').strip()
            elif line.startswith('CTA:'):
                cta = line.replace('CTA:', '').strip()
                
        return {
            "hashtags": hashtags,
            "cta": cta
        }
    
    except Exception as e:
        print(f"Error communicating with Groq: {e}")
        # Return graceful fallbacks so the bot doesn't crash
        return {
            "hashtags": "#mememwitu #memesdaily #funnymemes #trending #viral",
            "cta": "Like and follow us for more unmatched meme energy! 😂👇"
        }

if __name__ == "__main__":
    # Test script output
    test_caption = "Me looking at my bank account on the 10th of the month"
    result = enhance_vibe(test_caption)
    print("Testing Groq AI generation..")
    print(f"Hashtags: {result['hashtags']}")
    print(f"CTA: {result['cta']}")
