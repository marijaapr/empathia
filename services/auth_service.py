import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


class AuthService:
    """Supabase Authentication Service"""
    
    @staticmethod
    def sign_up(email: str, password: str, username: str = None):
        """Sign up new user"""
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def sign_in(email: str, password: str):
        """Sign in user"""
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
                "access_token": response.session.access_token if response.session else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def sign_out(access_token: str):
        """Sign out user"""
        try:
            # Create client with user's access token for logout
            supabase_user = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            supabase_user.auth.set_session(access_token, "")
            supabase_user.auth.sign_out()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def verify_token(access_token: str):
        """Verify JWT with Supabase Auth (Supabase v2: use get_user(jwt=), not set_session)."""
        if not access_token or not str(access_token).strip():
            return {"success": False, "error": "No token provided"}
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            return {"success": False, "error": "Supabase auth not configured"}

        token = str(access_token).strip()
        try:
            client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            response = client.auth.get_user(jwt=token)
            user = getattr(response, "user", None) if response is not None else None
            if user is None:
                return {"success": False, "error": "Invalid token"}
            user_id = getattr(user, "id", None)
            if not user_id:
                return {"success": False, "error": "User id not found"}
            return {
                "success": True,
                "user": user,
                "user_id": str(user_id),
            }
        except Exception as e:
            print(f"verify_token error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def refresh_session(refresh_token: str):
        """Refresh access token"""
        try:
            response = supabase.auth.refresh_session(refresh_token)
            return {
                "success": True,
                "session": response.session,
                "access_token": response.session.access_token if response.session else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
