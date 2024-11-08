from supabase import create_client
import os
from dotenv import load_dotenv
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase environment variables")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {str(e)}")
    raise
  