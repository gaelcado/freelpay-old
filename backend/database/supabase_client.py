from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

load_dotenv()

try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {str(e)}")
    raise
  