import os
from supabase import create_client, Client
from datetime import datetime, timedelta

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class SupabaseDB:
    """Supabase database operations"""
    
    @staticmethod
    def get_or_create_user(user_id: str, email: str, username: str = None):
        """Get or create user in public.users table"""
        try:
            response = supabase.table("users").select("*").eq("id", user_id).execute()
            if response.data:
                return response.data[0]
            
            user_data = {
                "id": user_id,
                "email": email,
                "username": username or email.split("@")[0],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("users").insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error in get_or_create_user: {e}")
            return None

    @staticmethod
    def add_message(user_id: str, role: str, content: str, persona: str, language: str, mood_detected: str = None):
        """Add message to chat history"""
        try:
            message_data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "persona": persona,
                "language": language,
                "mood_detected": mood_detected,
                "created_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("messages").insert(message_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error in add_message: {e}")
            return None

    @staticmethod
    def get_chat_history(user_id: str, limit: int = 50):
        """Get user's chat history"""
        try:
            response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error in get_chat_history: {e}")
            return []

    @staticmethod
    def add_mood_entry(user_id: str, mood: str, intensity: int):
        """Add mood entry"""
        try:
            mood_data = {
                "user_id": user_id,
                "mood": mood,
                "intensity": intensity,
                "created_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("mood_entries").insert(mood_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error in add_mood_entry: {e}")
            return None

    @staticmethod
    def get_mood_history(user_id: str, days: int = 30):
        """Get mood history for specified days"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            response = supabase.table("mood_entries").select("mood, intensity, created_at").eq("user_id", user_id).gte("created_at", start_date).execute()
            
            # Group by date and mood
            mood_data = {}
            for entry in response.data:
                date = entry["created_at"][:10]
                mood = entry["mood"]
                if date not in mood_data:
                    mood_data[date] = {}
                if mood not in mood_data[date]:
                    mood_data[date][mood] = {"count": 0, "avg_intensity": 0, "intensities": []}
                
                mood_data[date][mood]["count"] += 1
                mood_data[date][mood]["intensities"].append(entry["intensity"])
            
            # Calculate averages
            for date in mood_data:
                for mood in mood_data[date]:
                    intensities = mood_data[date][mood]["intensities"]
                    mood_data[date][mood]["avg_intensity"] = sum(intensities) / len(intensities)
                    del mood_data[date][mood]["intensities"]
            
            return mood_data
        except Exception as e:
            print(f"Error in get_mood_history: {e}")
            return {}

    @staticmethod
    def get_weekly_mood_summary(user_id: str):
        """Get 7-day mood summary"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            response = supabase.table("mood_entries").select("mood, intensity").eq("user_id", user_id).gte("created_at", start_date).execute()
            
            mood_summary = {}
            for entry in response.data:
                mood = entry["mood"]
                if mood not in mood_summary:
                    mood_summary[mood] = {"count": 0, "intensities": []}
                mood_summary[mood]["count"] += 1
                mood_summary[mood]["intensities"].append(entry["intensity"])
            
            # Calculate averages
            for mood in mood_summary:
                intensities = mood_summary[mood]["intensities"]
                mood_summary[mood]["avg_intensity"] = sum(intensities) / len(intensities)
                del mood_summary[mood]["intensities"]
            
            return mood_summary
        except Exception as e:
            print(f"Error in get_weekly_mood_summary: {e}")
            return {}

    @staticmethod
    def create_chat_session(user_id: str, title: str = None):
        """Create a new chat session"""
        try:
            session_data = {
                "user_id": user_id,
                "title": title or f"Chat on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("chat_sessions").insert(session_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error in create_chat_session: {e}")
            return None

    @staticmethod
    def get_user_chat_sessions(user_id: str, limit: int = 100):
        """Get all chat sessions for a user"""
        try:
            response = supabase.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error in get_user_chat_sessions: {e}")
            return []

    @staticmethod
    def get_session_messages(session_id: str, limit: int = 50):
        """Get messages for a specific chat session"""
        try:
            response = supabase.table("session_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error in get_session_messages: {e}")
            return []

    @staticmethod
    def add_session_message(session_id: str, user_id: str, role: str, content: str, persona: str, language: str, mood_detected: str = None):
        """Add message to a specific chat session"""
        try:
            message_data = {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "persona": persona,
                "language": language,
                "mood_detected": mood_detected,
                "created_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("session_messages").insert(message_data).execute()
            # Update session updated_at
            supabase.table("chat_sessions").update({"updated_at": datetime.utcnow().isoformat()}).eq("id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error in add_session_message: {e}")
            return None

    @staticmethod
    def delete_chat_session(session_id: str):
        """Delete a chat session and all its messages"""
        try:
            # Delete all messages in this session (cascade will handle it, but being explicit)
            supabase.table("session_messages").delete().eq("session_id", session_id).execute()
            # Delete the session
            response = supabase.table("chat_sessions").delete().eq("id", session_id).execute()
            return True
        except Exception as e:
            print(f"Error in delete_chat_session: {e}")
            return False

    @staticmethod
    def get_user_role(user_id: str) -> str:
        """Get user role by checking if they have a psychologist profile"""
        try:
            # Check if user has a psychologist profile
            response = supabase.table("psychologist_profiles").select("id").eq("user_id", user_id).execute()
            if response.data and len(response.data) > 0:
                return "psychologist"
            return "user"
        except Exception as e:
            print(f"Error in get_user_role: {e}")
            return "user"
