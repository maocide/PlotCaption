import os
import base64
import requests
import tiktoken
from openai import OpenAI
from typing import Optional, List, Dict, Union, Any


# --- Utility Functions ---

def num_tokens_from_string(text: str, model_name: str) -> int:
    """
    Calculates the number of tokens in a given string using a specific model's tokenizer.

    Args:
        text (str): The string to tokenize.
        model_name (str): The name of the model to use for encoding (e.g., "gpt-4o", "gpt-3.5-turbo").

    Returns:
        int: The number of tokens in the string.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception as e:
        print(f"Warning: Could not get token count for model {model_name}. Error: {e}")
        return 0  # Or raise an error, depending on desired behavior


def _encode_bytes_to_base64(content_bytes: bytes) -> str:
    """
    Encodes raw image bytes to a base64 string (UTF-8 decoded).

    Args:
        content_bytes (bytes): The raw bytes of an image.

    Returns:
        str: The base64 encoded string.
    """
    return base64.b64encode(content_bytes).decode('utf-8')


# --- Internal AI Call Helper ---

def _make_api_call(
        client: OpenAI,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        **kwargs: Any  # For any other model-specific or future parameters
) -> Optional[str]:
    """
    Internal helper to execute the OpenAI chat completion API call.

    Args:
        client (OpenAI): The initialized OpenAI client.
        model (str): The name of the AI model to use.
        messages (List[Dict[str, Any]]): The list of message objects.
        stream (bool): Whether to stream the response. Defaults to False.
        max_tokens (Optional[int]): The maximum number of tokens to generate.
        temperature (Optional[float]): Controls randomness (0.0-2.0).
        top_p (Optional[float]): Nucleus sampling (0.0-1.0).
        frequency_penalty (Optional[float]): Penalizes new tokens based on their existing frequency in the text.
        presence_penalty (Optional[float]): Penalizes new tokens based on whether they appear in the text so far.
        kwargs (Any): Additional keyword arguments to pass directly to client.chat.completions.create.

    Returns:
        Optional[str]: The content of the first choice's message, or None if no valid response.
    """
    try:
        call_params = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        if temperature is not None:
            call_params["temperature"] = temperature
        if top_p is not None:
            call_params["top_p"] = top_p
        if frequency_penalty is not None:
            call_params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            call_params["presence_penalty"] = presence_penalty

        # Add any extra kwargs directly
        call_params.update(kwargs)

        response = client.chat.completions.create(**call_params)

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        return None

    except Exception as e:
        print(f"Error during AI API call: {e}")
        return None


# --- Public API Wrapper Functions ---

def call_text_model(
        api_key: str,
        base_url: str,
        model: str,
        user_request: str,  # Renamed from 'data' for clarity
        system_prompt: Optional[str] = None,  # Renamed from 'request' for clarity
        **kwargs: Any  # Accepts all common params and other kwargs from _make_api_call
) -> Optional[str]:
    """
    Calls an LLM for text-only chat completions.

    Args:
        api_key (str): Your API key.
        base_url (str): The base URL for the API endpoint (e.g., "https://api.openai.com/v1").
        model (str): The name of the AI model (e.g., "gpt-4o", "gemini-1.5-flash").
        user_request (str): The user's prompt/query.
        system_prompt (Optional[str]): An optional system message to set context/role.
        kwargs (Any): Additional parameters for the API call (e.g., temperature, max_tokens, top_p, etc.).

    Returns:
        Optional[str]: The generated text response.
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_request})

    return _make_api_call(client, model, messages, **kwargs)


def call_image_model(
        api_key: str,
        base_url: str,
        model: str,
        image_source: Union[str, bytes],  # Can be file path, URL, or raw bytes
        user_request: str,
        safe_settings: Optional[List[Dict[str, Any]]] = None,  # For models like Gemini
        **kwargs: Any  # Accepts all common params and other kwargs from _make_api_call
) -> Optional[str]:
    """
    Calls a VLM for image analysis, handling image input from a file path, URL, or raw bytes.

    Args:
        api_key (str): Your API key.
        base_url (str): The base URL for the API endpoint.
        model (str): The name of the VLM model (e.g., "gpt-4o", "gemini-1.5-flash-latest").
        image_source (Union[str, bytes]): Path to a local image file, a URL, or raw image bytes.
        user_request (str): The textual request for the VLM.
        safe_settings (Optional[List[Dict[str, Any]]]): List of dictionaries for content safety settings (e.g., for Gemini via OpenAI-compatible APIs).
        kwargs (Any): Additional parameters for the API call (e.g., temperature, max_tokens, top_p, etc.).

    Returns:
        Optional[str]: The VLM's analysis of the image.
    """
    client = OpenAI(api_key=api_key, base_url=base_url)
    encoded_image: str

    if isinstance(image_source, bytes):
        # Already bytes, just encode
        encoded_image = _encode_bytes_to_base64(image_source)
    elif os.path.isfile(image_source):
        # It's a file path
        with open(image_source, "rb") as image_file:
            encoded_image = _encode_bytes_to_base64(image_file.read())
    elif image_source.startswith(('http://', 'https://')):
        # It's a URL, download content to memory
        try:
            response = requests.get(image_source)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            encoded_image = _encode_bytes_to_base64(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image from URL {image_source}: {e}")
            return None
    else:
        print("Invalid image_source: Must be a file path, URL, or bytes.")
        return None

    # Construct the messages list. The 'safe' parameter is part of the user message dict.
    user_message_content = [
        {"type": "text", "text": user_request},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}},
    ]

    user_message_dict: Dict[str, Any] = {
        "role": "user",
        "content": user_message_content,
    }

    if safe_settings:
        # Example of how 'safe' settings are structured for some models (like Gemini)
        # Note: This is *not* a standard OpenAI parameter for all models.
        # It needs to be inside the user message dictionary.
        user_message_dict["safe"] = safe_settings
        # The 'safe' block provided in original code example
        # user_message_dict["safe"] = [
        #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        # ]

    messages = [user_message_dict]

    return _make_api_call(client, model, messages, **kwargs)