"""
Psychologist Service Module
Handles all psychologist-related database operations and business logic
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import os
from supabase import create_client, Client


class PsychologistService:
    """Service class for psychologist operations"""

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        )

    # ========== PSYCHOLOGIST PROFILE OPERATIONS ==========

    async def create_psychologist_profile(
        self,
        user_id: str,
        full_name: str,
        specializations: List[str],
        bio: Optional[str] = None,
        license_number: Optional[str] = None,
        years_of_experience: Optional[int] = None,
        languages_spoken: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new psychologist profile
        
        Args:
            user_id: UUID of the user
            full_name: Full name of psychologist
            specializations: List of specialization areas
            bio: Professional biography
            license_number: Professional license number
            years_of_experience: Years of experience
            languages_spoken: Languages the psychologist speaks
            
        Returns:
            Created profile data
        """
        try:
            response = self.supabase.table("psychologist_profiles").insert({
                "user_id": user_id,
                "full_name": full_name,
                "specializations": specializations,
                "bio": bio,
                "license_number": license_number,
                "years_of_experience": years_of_experience,
                "languages_spoken": languages_spoken or ["English"]
            }).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating psychologist profile: {str(e)}")
            raise

    async def update_psychologist_profile(
        self,
        user_id: str,
        **kwargs
    ) -> Dict:
        """
        Update psychologist profile
        
        Args:
            user_id: UUID of the user
            **kwargs: Fields to update
            
        Returns:
            Updated profile data
        """
        try:
            # Add updated_at timestamp
            kwargs['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.supabase.table("psychologist_profiles").update(
                kwargs
            ).eq("user_id", user_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating psychologist profile: {str(e)}")
            raise

    async def get_psychologist_profile(self, user_id: str) -> Dict:
        """
        Get psychologist profile by user_id
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Profile data
        """
        try:
            response = self.supabase.table("psychologist_profiles").select(
                "*"
            ).eq("user_id", user_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching psychologist profile: {str(e)}")
            raise

    async def get_psychologist_by_id(self, psychologist_id: str) -> Dict:
        """
        Get psychologist profile by psychologist_id
        
        Args:
            psychologist_id: UUID of the psychologist profile
            
        Returns:
            Profile data
        """
        try:
            response = self.supabase.table("psychologist_profiles_with_stats").select(
                "*"
            ).eq("id", psychologist_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching psychologist by ID: {str(e)}")
            raise

    async def toggle_psychologist_online_status(
        self,
        user_id: str,
        is_online: bool
    ) -> Dict:
        """
        Toggle psychologist online/offline status
        
        Args:
            user_id: UUID of the user
            is_online: Boolean for online status
            
        Returns:
            Updated profile data
        """
        try:
            response = self.supabase.table("psychologist_profiles").update({
                "is_online": is_online,
                "last_online_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error toggling online status: {str(e)}")
            raise

    # ========== PSYCHOLOGIST SEARCH & DISCOVERY ==========

    async def search_psychologists(
        self,
        specializations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        is_online_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        Search for psychologists with filters
        
        Args:
            specializations: Filter by specializations
            languages: Filter by languages
            min_rating: Minimum average rating
            is_online_only: Only show online psychologists
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Tuple of (psychologists, total_count)
        """
        try:
            query = self.supabase.table("psychologist_profiles_with_stats").select(
                "*"
            )
            
            # Apply filters
            if is_online_only:
                query = query.eq("is_online", True)
            
            if specializations:
                # Filter by specializations (contains any)
                for spec in specializations:
                    query = query.ilike("specializations", f"%{spec}%")
            
            if languages:
                # Filter by languages (contains any)
                for lang in languages:
                    query = query.ilike("languages_spoken", f"%{lang}%")
            
            if min_rating is not None:
                query = query.gte("average_rating", min_rating)
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            response = query.execute()
            
            # Get total count
            count_response = self.supabase.table(
                "psychologist_profiles_with_stats"
            ).select("id", count="exact").execute()
            
            return response.data, len(count_response.data)
        except Exception as e:
            print(f"Error searching psychologists: {str(e)}")
            raise

    async def get_recommended_psychologists(
        self,
        detected_specializations: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Get recommended psychologists based on emotional state
        
        Args:
            detected_specializations: Specializations needed
            limit: Number of recommendations
            
        Returns:
            List of recommended psychologists
        """
        try:
            # First, try to get online psychologists with matching specializations
            response = self.supabase.table(
                "recommended_psychologists"
            ).select(
                "*"
            ).eq("is_online", True).limit(limit).execute()
            
            # If fewer than needed, add offline ones
            if len(response.data) < limit:
                offline_response = self.supabase.table(
                    "recommended_psychologists"
                ).select(
                    "*"
                ).eq("is_online", False).limit(
                    limit - len(response.data)
                ).execute()
                
                response.data.extend(offline_response.data)
            
            return response.data
        except Exception as e:
            print(f"Error getting recommended psychologists: {str(e)}")
            raise

    # ========== CHAT REQUEST OPERATIONS ==========

    async def create_chat_request(
        self,
        user_id: str,
        psychologist_id: str,
        message: Optional[str] = None,
        urgency_level: str = "medium"
    ) -> Dict:
        """
        Create a chat request from user to psychologist
        
        Args:
            user_id: UUID of the user
            psychologist_id: UUID of the psychologist profile
            message: Optional message with request
            urgency_level: 'low', 'medium', or 'high'
            
        Returns:
            Created request data
        """
        try:
            response = self.supabase.table("psychologist_chat_requests").insert({
                "user_id": user_id,
                "psychologist_id": psychologist_id,
                "message": message,
                "urgency_level": urgency_level,
                "status": "pending"
            }).execute()
            
            request_data = response.data[0] if response.data else None
            
            # Create notification for psychologist
            if request_data:
                await self._create_notification(
                    psychologist_id=psychologist_id,
                    type="request_received",
                    title="New Chat Request",
                    message=f"A user has requested to chat with you",
                    request_id=request_data["id"],
                    related_user_id=user_id
                )
            
            return request_data
        except Exception as e:
            print(f"Error creating chat request: {str(e)}")
            raise

    async def get_pending_requests_for_psychologist(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get pending chat requests for a psychologist
        
        Args:
            user_id: UUID of the psychologist user
            limit: Number of requests
            
        Returns:
            List of pending requests
        """
        try:
            # Get psychologist ID from user_id
            psychologist = await self.get_psychologist_profile(user_id)
            
            if not psychologist:
                return []
            
            response = self.supabase.table("psychologist_chat_requests").select(
                "*"
            ).eq("psychologist_id", psychologist["id"]).eq(
                "status", "pending"
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching pending requests: {str(e)}")
            raise

    async def accept_chat_request(
        self,
        request_id: str,
        user_id: str
    ) -> Dict:
        """
        Accept a chat request and create a session
        
        Args:
            request_id: UUID of the request
            user_id: UUID of the psychologist user
            
        Returns:
            Session data
        """
        try:
            # Update request status
            request_response = self.supabase.table(
                "psychologist_chat_requests"
            ).update({
                "status": "accepted",
                "responded_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
            
            request_data = request_response.data[0]
            
            # Get user name for session title
            user_name = "User"
            try:
                user_response = self.supabase.table('users').select('full_name, username, email').eq('id', request_data["user_id"]).limit(1).execute()
                if user_response.data:
                    user_data = user_response.data[0]
                    user_name = user_data.get('full_name') or user_data.get('username') or (user_data.get('email', '').split('@')[0] if user_data.get('email') else 'User')
            except Exception as user_err:
                print(f"⚠️ Could not fetch user name: {str(user_err)}")
            
            # Create session
            session_response = self.supabase.table(
                "psychologist_sessions"
            ).insert({
                "request_id": request_id,
                "user_id": request_data["user_id"],
                "psychologist_id": request_data["psychologist_id"],
                "title": f"Session with {user_name}"
            }).execute()
            
            session_data = session_response.data[0] if session_response.data else None
            
            # Create notification for user
            if session_data:
                await self._create_notification(
                    user_id=request_data["user_id"],
                    type="request_accepted",
                    title="Chat Request Accepted",
                    message="A psychologist has accepted your request",
                    session_id=session_data["id"]
                )
            
            return session_data
        except Exception as e:
            print(f"Error accepting chat request: {str(e)}")
            raise

    async def reject_chat_request(
        self,
        request_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Reject a chat request
        
        Args:
            request_id: UUID of the request
            user_id: UUID of the psychologist user
            reason: Optional reason for rejection
            
        Returns:
            Updated request data
        """
        try:
            request_response = self.supabase.table(
                "psychologist_chat_requests"
            ).select("*").eq("id", request_id).execute()
            
            request_data = request_response.data[0]
            
            # Update request status
            update_response = self.supabase.table(
                "psychologist_chat_requests"
            ).update({
                "status": "rejected",
                "responded_at": datetime.utcnow().isoformat(),
                "response_note": reason
            }).eq("id", request_id).execute()
            
            # Create notification for user
            await self._create_notification(
                user_id=request_data["user_id"],
                type="request_rejected",
                title="Chat Request Declined",
                message=reason or "Your chat request has been declined"
            )
            
            return update_response.data[0] if update_response.data else None
        except Exception as e:
            print(f"Error rejecting chat request: {str(e)}")
            raise

    # ========== SESSION MESSAGE OPERATIONS ==========

    async def send_session_message(
        self,
        session_id: str,
        sender_id: str,
        content: str
    ) -> Dict:
        """
        Send a message in a psychologist session
        
        Args:
            session_id: UUID of the session
            sender_id: UUID of the sender
            content: Message content
            
        Returns:
            Created message data
        """
        try:
            # Insert the message
            response = self.supabase.table("psychologist_session_messages").insert({
                "session_id": session_id,
                "sender_id": sender_id,
                "content": content,
                "message_type": "text"
            }).execute()
            
            # Get current session to increment message count
            session_response = self.supabase.table("psychologist_sessions").select(
                "message_count"
            ).eq("id", session_id).execute()
            
            if session_response.data:
                current_count = session_response.data[0].get("message_count", 0)
                # Increment message count in session
                self.supabase.table("psychologist_sessions").update({
                    "message_count": current_count + 1
                }).eq("id", session_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error sending session message: {str(e)}")
            raise

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get messages from a session, including messages from the original chat session
        
        Args:
            session_id: UUID of the psychologist session
            limit: Number of messages
            offset: Pagination offset
            
        Returns:
            List of messages (combines original chat + psychologist messages)
        """
        try:
            # Get the psychologist session details to check for chat_session_id
            session_response = self.supabase.table("psychologist_sessions").select(
                "id, chat_session_id"
            ).eq("id", session_id).single().execute()
            
            if not session_response.data:
                return []
            
            session = session_response.data
            chat_session_id = session.get('chat_session_id')
            
            all_messages = []
            
            # If linked to original chat session, get those messages first
            if chat_session_id:
                print(f"📥 Loading original chat messages from session: {chat_session_id}")
                try:
                    chat_response = self.supabase.table("session_messages").select(
                        "id, session_id, role, content, created_at"
                    ).eq("session_id", chat_session_id).order(
                        "created_at", desc=False
                    ).execute()
                    
                    # Convert chat messages to psychologist message format
                    for msg in chat_response.data:
                        all_messages.append({
                            'id': msg['id'],
                            'session_id': session_id,  # Use psychologist session ID
                            'sender_id': msg.get('role'),  # 'user' or 'assistant'
                            'content': msg['content'],
                            'created_at': msg['created_at'],
                            'is_from_original_chat': True  # Flag to identify origin
                        })
                    
                    print(f"✅ Loaded {len(chat_response.data)} messages from original chat")
                except Exception as e:
                    print(f"⚠️ Could not load original chat messages: {e}")
            
            # Get psychologist session messages
            psych_response = self.supabase.table(
                "psychologist_session_messages"
            ).select(
                "*"
            ).eq("session_id", session_id).order(
                "created_at", desc=False
            ).execute()
            
            # Add psychologist messages
            for msg in psych_response.data:
                msg['is_from_original_chat'] = False
                all_messages.append(msg)
            
            print(f"✅ Loaded {len(psych_response.data)} psychologist messages")
            
            # Sort all messages by created_at
            all_messages.sort(key=lambda x: x['created_at'])
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return all_messages[start:end]
            
        except Exception as e:
            print(f"Error fetching session messages: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def mark_message_as_read(self, message_id: str) -> Dict:
        """
        Mark a message as read
        
        Args:
            message_id: UUID of the message
            
        Returns:
            Updated message data
        """
        try:
            response = self.supabase.table(
                "psychologist_session_messages"
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow().isoformat()
            }).eq("id", message_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error marking message as read: {str(e)}")
            raise

    # ========== SESSION OPERATIONS ==========

    async def end_psychologist_session(
        self,
        session_id: str,
        session_notes: Optional[str] = None,
        follow_up_required: bool = False,
        follow_up_date: Optional[str] = None
    ) -> Dict:
        """
        End a psychologist session
        
        Args:
            session_id: UUID of the session
            session_notes: Optional notes from psychologist
            follow_up_required: Whether follow-up is needed
            follow_up_date: Date for follow-up
            
        Returns:
            Updated session data
        """
        try:
            update_data = {
                "ended_at": datetime.utcnow().isoformat(),
                "session_notes": session_notes,
                "follow_up_required": follow_up_required
            }
            
            if follow_up_date:
                update_data["follow_up_date"] = follow_up_date
            
            response = self.supabase.table("psychologist_sessions").update(
                update_data
            ).eq("id", session_id).execute()
            
            # Mark request as completed
            session_data = response.data[0]
            if session_data:
                self.supabase.table("psychologist_chat_requests").update({
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat()
                }).eq("id", session_data["request_id"]).execute()
            
            return session_data
        except Exception as e:
            print(f"Error ending session: {str(e)}")
            raise

    async def get_user_active_sessions(self, user_id: str) -> List[Dict]:
        """
        Get active sessions for a user
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of active sessions
        """
        try:
            response = self.supabase.table("psychologist_sessions").select(
                "*"
            ).eq("user_id", user_id).is_("ended_at", "null").execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching active sessions: {str(e)}")
            raise

    async def get_psychologist_active_sessions(self, user_id: str) -> List[Dict]:
        """
        Get active sessions for a psychologist
        
        Args:
            user_id: UUID of the psychologist user
            
        Returns:
            List of active sessions (only those with valid chat_session_id)
        """
        try:
            # Get psychologist ID
            psychologist = await self.get_psychologist_profile(user_id)
            
            if not psychologist:
                print(f"⚠️ No psychologist profile found for user_id: {user_id}")
                return []
            
            print(f"🔍 Fetching active sessions for psychologist_id: {psychologist['id']}")
            
            # Only get sessions that have a chat_session_id (new architecture)
            # Filter out old sessions without chat_session_id
            response = self.supabase.table("psychologist_sessions").select(
                "*"
            ).eq("psychologist_id", psychologist["id"]).is_(
                "ended_at", "null"
            ).not_.is_("chat_session_id", "null").execute()
            
            sessions = response.data or []
            print(f"✅ Found {len(sessions)} active psychologist_sessions (with chat_session_id)")
            for session in sessions:
                print(f"   → Session ID: {session.get('id')}, chat_session_id: {session.get('chat_session_id')}, ended_at: {session.get('ended_at')}")
            
            # Enrich each session with user name
            enriched_sessions = []
            for session in sessions:
                # Get user name from users table
                session_user_id = session.get('user_id')
                user_name = 'Anonymous User'
                
                if session_user_id:
                    try:
                        user_response = self.supabase.table('users').select('full_name, email, username').eq('id', session_user_id).limit(1).execute()
                        if user_response.data:
                            user_data = user_response.data[0]
                            # Prefer full_name, then username, then email prefix
                            user_name = user_data.get('full_name') or user_data.get('username') or (user_data.get('email', '').split('@')[0] if user_data.get('email') else 'Anonymous User')
                    except Exception as user_err:
                        print(f"⚠️ Could not fetch user name for {session_user_id}: {str(user_err)}")
                
                # Add user_name to session data
                session['user_name'] = user_name
                enriched_sessions.append(session)
            
            return enriched_sessions
        except Exception as e:
            print(f"Error fetching psychologist active sessions: {str(e)}")
            raise

    async def get_psychologist_completed_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get completed sessions for a psychologist
        
        Args:
            user_id: UUID of the psychologist user
            limit: Maximum number of sessions to return
            
        Returns:
            List of completed sessions
        """
        try:
            # Get psychologist ID
            psychologist = await self.get_psychologist_profile(user_id)
            
            if not psychologist:
                print(f"⚠️ No psychologist profile found for user_id: {user_id}")
                return []
            
            print(f"🔍 Fetching completed sessions for psychologist_id: {psychologist['id']}")
            
            # Get sessions that have ended_at set (completed)
            response = self.supabase.table("psychologist_sessions").select(
                "*"
            ).eq("psychologist_id", psychologist["id"]).not_.is_(
                "ended_at", "null"
            ).order("ended_at", desc=True).limit(limit).execute()
            
            sessions = response.data or []
            print(f"✅ Found {len(sessions)} completed psychologist_sessions")
            
            # Enrich each session with user name
            enriched_sessions = []
            for session in sessions:
                # Get user name from users table
                user_id = session.get('user_id')
                user_name = 'Anonymous User'
                
                if user_id:
                    try:
                        user_response = self.supabase.table('users').select('full_name, email, username').eq('id', user_id).limit(1).execute()
                        if user_response.data:
                            user_data = user_response.data[0]
                            # Prefer full_name, then username, then email prefix
                            user_name = user_data.get('full_name') or user_data.get('username') or (user_data.get('email', '').split('@')[0] if user_data.get('email') else 'Anonymous User')
                    except Exception as user_err:
                        print(f"⚠️ Could not fetch user name for {user_id}: {str(user_err)}")
                
                # Add user_name to session data
                session['user_name'] = user_name
                enriched_sessions.append(session)
            
            return enriched_sessions
        except Exception as e:
            print(f"Error fetching psychologist completed sessions: {str(e)}")
            raise

    async def get_psychologist_ratings(self, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get ratings for a psychologist
        
        Args:
            user_id: UUID of the psychologist user
            limit: Maximum number of ratings to return
            
        Returns:
            List of ratings
        """
        try:
            # Get psychologist ID
            psychologist = await self.get_psychologist_profile(user_id)
            
            if not psychologist:
                print(f"⚠️ No psychologist profile found for user_id: {user_id}")
                return []
            
            print(f"🔍 Fetching ratings for psychologist_id: {psychologist['id']}")
            print(f"🔍 Also checking for user_id: {user_id}")
            
            # Get ratings - check both psychologist_profile.id and user_id for backward compatibility
            # This handles both old ratings (saved with user_id) and new ratings (saved with profile.id)
            response = self.supabase.table("psychologist_ratings").select(
                "*"
            ).or_(f"psychologist_id.eq.{psychologist['id']},psychologist_id.eq.{user_id}").order(
                "created_at", desc=True
            ).limit(limit).execute()
            
            print(f"✅ Found {len(response.data) if response.data else 0} ratings")
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching psychologist ratings: {str(e)}")
            raise

    # ========== RATING & REVIEW OPERATIONS ==========

    async def create_rating(
        self,
        psychologist_id: str,
        user_id: str,
        rating: float,
        review_text: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Create a rating/review for a psychologist
        
        Args:
            psychologist_id: UUID of the psychologist
            user_id: UUID of the user
            rating: Rating value (1-5)
            review_text: Optional review text
            session_id: Optional session ID
            
        Returns:
            Created rating data
        """
        try:
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
            
            response = self.supabase.table("psychologist_ratings").insert({
                "psychologist_id": psychologist_id,
                "user_id": user_id,
                "rating": rating,
                "review_text": review_text,
                "session_id": session_id
            }).execute()
            
            # Create notification for psychologist
            if response.data:
                await self._create_notification(
                    psychologist_id=psychologist_id,
                    type="new_rating",
                    title="New Rating",
                    message=f"You received a {rating}-star rating"
                )
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating rating: {str(e)}")
            raise

    async def get_psychologist_reviews(
        self,
        psychologist_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get reviews for a psychologist
        
        Args:
            psychologist_id: UUID of the psychologist
            limit: Number of reviews
            
        Returns:
            List of reviews
        """
        try:
            response = self.supabase.table("psychologist_ratings").select(
                "*"
            ).eq("psychologist_id", psychologist_id).order(
                "created_at", desc=True
            ).limit(limit).execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            raise

    # ========== NOTIFICATION OPERATIONS ==========

    async def _create_notification(
        self,
        user_id: Optional[str] = None,
        psychologist_id: Optional[str] = None,
        type: str = "message_received",
        title: str = "Notification",
        message: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        related_user_id: Optional[str] = None
    ) -> Dict:
        """
        Create a notification (internal method)
        
        Args:
            user_id: UUID of the user
            psychologist_id: UUID of the psychologist (will resolve to user_id)
            type: Notification type
            title: Notification title
            message: Notification message
            request_id: Related request ID
            session_id: Related session ID
            related_user_id: ID of related user
            
        Returns:
            Created notification data
        """
        try:
            # If psychologist_id provided, resolve to user_id
            if psychologist_id and not user_id:
                psychologist = await self.get_psychologist_by_id(psychologist_id)
                user_id = psychologist["user_id"] if psychologist else None
            
            if not user_id:
                return None
            
            response = self.supabase.table("notifications").insert({
                "user_id": user_id,
                "type": type,
                "title": title,
                "message": message,
                "request_id": request_id,
                "session_id": session_id,
                "related_user_id": related_user_id
            }).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating notification: {str(e)}")
            raise

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get notifications for a user
        
        Args:
            user_id: UUID of the user
            unread_only: Only get unread notifications
            limit: Number of notifications
            
        Returns:
            List of notifications
        """
        try:
            query = self.supabase.table("notifications").select(
                "*"
            ).eq("user_id", user_id).order("created_at", desc=True)
            
            if unread_only:
                query = query.eq("is_read", False)
            
            response = query.limit(limit).execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching notifications: {str(e)}")
            raise

    async def mark_notification_as_read(self, notification_id: str) -> Dict:
        """
        Mark notification as read
        
        Args:
            notification_id: UUID of the notification
            
        Returns:
            Updated notification data
        """
        try:
            response = self.supabase.table("notifications").update({
                "is_read": True,
                "read_at": datetime.utcnow().isoformat()
            }).eq("id", notification_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error marking notification as read: {str(e)}")
            raise
