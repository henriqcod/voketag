"""
Token generator - Generates signed tokens for products in batch.
Uses HMAC-SHA256 for cryptographic signatures.
"""

import asyncio
import hmac
import hashlib
import base64
from typing import List
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from factory_service.config.settings import settings
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)


def generate_single_token(product_id: str = None) -> str:
    """
    Generate a single signed token.
    
    Args:
        product_id: Optional product ID (generates new UUID if not provided)
    
    Returns:
        Signed token (Base64 URL-safe)
    """
    if product_id is None:
        product_id = str(uuid4())
    
    # Create payload: product_id
    payload = product_id.encode('utf-8')
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        settings.hmac_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).digest()
    
    # Combine payload + signature
    token_bytes = payload + b':' + signature
    
    # Encode as Base64 URL-safe
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
    
    return token


async def generate_tokens_batch(count: int) -> List[str]:
    """
    Generate tokens in batch using parallel processing.
    
    Args:
        count: Number of tokens to generate
    
    Returns:
        List of signed tokens
    """
    logger.info(f"Generating {count} tokens in batch...")
    
    # Use ThreadPoolExecutor for CPU-bound token generation
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Generate tokens in parallel
        futures = [
            loop.run_in_executor(executor, generate_single_token)
            for _ in range(count)
        ]
        
        tokens = await asyncio.gather(*futures)
    
    logger.info(f"Generated {len(tokens)} tokens")
    return tokens


def verify_token(token: str) -> tuple[bool, str]:
    """
    Verify token signature.
    
    Args:
        token: Signed token
    
    Returns:
        Tuple of (is_valid, product_id)
    """
    try:
        # Decode Base64
        # Add padding if needed
        padding = 4 - (len(token) % 4)
        if padding != 4:
            token += '=' * padding
        
        token_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
        
        # Split payload and signature
        payload, signature = token_bytes.rsplit(b':', 1)
        
        # Verify signature
        expected_signature = hmac.new(
            settings.hmac_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
        
        # Constant-time comparison
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if is_valid:
            product_id = payload.decode('utf-8')
            return True, product_id
        else:
            return False, None
            
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return False, None


# Batch token generation with performance tracking
async def generate_tokens_batch_with_metrics(count: int) -> dict:
    """
    Generate tokens with performance metrics.
    
    Args:
        count: Number of tokens to generate
    
    Returns:
        Dict with tokens and metrics
    """
    from datetime import datetime
    
    start_time = datetime.utcnow()
    
    tokens = await generate_tokens_batch(count)
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
    return {
        "tokens": tokens,
        "count": len(tokens),
        "elapsed_seconds": elapsed,
        "tokens_per_second": len(tokens) / elapsed if elapsed > 0 else 0,
    }
