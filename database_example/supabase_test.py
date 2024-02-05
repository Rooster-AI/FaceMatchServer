import os
from supabase import create_client, Client

url: str = "https://njmckcmrwmpmwdnfxxsj.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbWNrY21yd21wbXdkbmZ4eHNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcxNjQyOTEsImV4cCI6MjAyMjc0MDI5MX0.eVKm1TuiJ8E5qTt3FLlEnNjsLtbcBv0mx3g1bTA94Fw"

supabase: Client = create_client(url, key)



response = supabase.table('stores').select("*").execute()

print(response)

