"""Supabase client initialization and helper."""

import logging
from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger("app.supabase")
settings = get_settings()

# Initialize Supabase client
supabase: Client = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY and settings.SUPABASE_URL != "your_supabase_url":
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase URL/Key not configured or using placeholders. Supabase operations will be skipped or mock data will be used.")
