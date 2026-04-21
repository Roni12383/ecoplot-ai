import openai
import os


def get_ai_response(user_input, metrics):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Please set your OPENAI_API_KEY environment variable."

    client = openai.OpenAI(api_key=api_key)

    context = f"""
    Context: Restoration site at Lat: {metrics['lat']}, Lon: {metrics['lon']}.
    Area: {metrics['area']} hectares. 
    Plant health (NDVI): {metrics['ndvi']}.
    Rainfall: {metrics['rain']}mm.
    Advice the farmer on next steps for restoration.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a restoration ecology expert."},
                {"role": "user", "content": context + "\nQuestion: " + user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
