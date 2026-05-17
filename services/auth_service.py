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
        """Verify if token is valid"""
        try:
            supabase_user = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            supabase_user.auth.set_session(access_token, "")
            user = supabase_user.auth.get_user(access_token)
            return {
                "success": True,
                "user": user
            }
        except Exception as e:
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
