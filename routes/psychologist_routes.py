"""
Psychologist API Routes
Flask blueprint for all psychologist-related endpoints
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import os
import asyncio
from typing import Dict, Optional

# Initialize blueprint
psychologist_bp = Blueprint('psychologist', __name__, url_prefix='/api/psychologist')

# Global services cache
_service_cache = {}

def run_async(coro):
    """Run an async coroutine in Flask context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop in current thread, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

def get_service(service_name):
    """Get cached service or create new one"""
    if service_name not in _service_cache:
        if service_name == 'psychologist':
            from services.psychologist.service import PsychologistService
            _service_cache[service_name] = PsychologistService()
        elif service_name == 'emotion':
            from services.emotion_analyzer import EmotionDetector
            _service_cache[service_name] = EmotionDetector()
    return _service_cache[service_name]

def with_services(f):
    """Decorator to inject services"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        psychologist_service = get_service('psychologist')
        emotion_detector = get_service('emotion')
        return f(psychologist_service, emotion_detector, *args, **kwargs)
    return decorated_function


# ============================================================================
# AUTHENTICATION & AUTHORIZATION HELPERS
# ============================================================================

def get_auth_user(request_headers: Dict) -> Optional[str]:
    """Verify JWT and return authenticated user id (ignores X-User-ID)."""
    from services.request_auth import get_authenticated_user_id
    return get_authenticated_user_id(request_headers)


def require_auth(f):
    """Decorator to require authentication and inject services"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_auth_user(request.headers)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        psychologist_service = get_service('psychologist')
        emotion_detector = get_service('emotion')
        return f(psychologist_service, emotion_detector, user_id, *args, **kwargs)
    return decorated_function


def require_psychologist_role(f):
    """Decorator to require psychologist role (psychologist_profiles row)."""
    @wraps(f)
    def decorated_function(psychologist_service, emotion_detector, user_id, *args, **kwargs):
        from database.supabase_db import SupabaseDB
        if SupabaseDB.get_user_role(user_id) != 'psychologist':
            return jsonify({"error": "Psychology student access required"}), 403
        return f(psychologist_service, emotion_detector, user_id, *args, **kwargs)
    return decorated_function


# ============================================================================
# PSYCHOLOGIST PROFILE ENDPOINTS
# ============================================================================

@psychologist_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user's psychologist profile - no auth required for testing"""
    try:
        from database.supabase_db import supabase
        
        # Get user_id from header or query param
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        print(f"👤 Fetching psychologist profile for user: {user_id}")
        
        # Get psychologist profile
        response = supabase.table('psychologist_profiles')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return jsonify({"error": "Profile not found"}), 404
        
        profile = response.data[0]
        print(f"✅ Found profile for {profile.get('full_name')}")
        
        return jsonify(profile), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error in get_profile: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/profile', methods=['POST'])
def create_profile():
    """Create new psychologist profile"""
    try:
        from database.supabase_db import supabase
        
        data = request.get_json()
        user_id = data.get('user_id') or request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'specializations']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        print(f"👤 Creating psychologist profile for user: {user_id}")
        
        # Create profile
        profile_data = {
            'user_id': user_id,
            'full_name': data['full_name'],
            'specializations': data.get('specializations', []),
            'bio': data.get('bio', ''),
            'years_of_experience': data.get('years_of_experience'),
            'languages_spoken': data.get('languages_spoken', ['English']),
            'is_online': data.get('is_online', False),
            'session_rate_usd': data.get('session_rate_usd', 0),
            'average_response_time_minutes': data.get('average_response_time_minutes', 30)
        }
        
        response = supabase.table('psychologist_profiles').insert(profile_data).execute()
        
        if response.data:
            print(f"✅ Profile created: {response.data[0].get('id')}")
            return jsonify(response.data[0]), 201
        else:
            return jsonify({"error": "Failed to create profile"}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error in create_profile: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update psychologist profile"""
    try:
        from database.supabase_db import supabase
        from supabase import create_client, Client
        import json
        import uuid
        from datetime import datetime
        import os
        
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not user_id:
            # Try to get from JSON body
            data = request.get_json() or {}
            user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        print(f"📝 Updating profile for user: {user_id}")
        print(f"🔑 Has auth token: {bool(auth_token)}")
        
        # Get data from JSON or form
        data = {}
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = request.form.to_dict()
        
        print(f"📝 Profile update data keys: {list(data.keys())}")
        
        # Handle file upload if present (optional)
        profile_image_url = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                try:
                    # Read file content
                    file_content = file.read()
                    file_ext = file.filename.split('.')[-1].lower()
                    
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_id = str(uuid.uuid4())[:8]
                    storage_path = f"psychologist_profiles/{user_id}/profile_{timestamp}_{unique_id}.{file_ext}"
                    
                    print(f"📤 Attempting to upload file to: {storage_path}")
                    print(f"📦 File size: {len(file_content)} bytes")
                    print(f"📄 Content type: {file.content_type}")
                    
                    try:
                        # Use service role with upsert - simpler and works with RLS
                        upload_response = supabase.storage.from_('psychologist-profiles').upload(
                            storage_path,
                            file_content,
                            {
                                "content-type": file.content_type or "image/jpeg",
                                "cache-control": "3600",
                                "upsert": "true"
                            }
                        )
                        
                        print(f"📤 Upload response: {upload_response}")
                        
                        # Get public URL
                        profile_image_url = supabase.storage.from_('psychologist-profiles').get_public_url(storage_path)
                        print(f"✅ Image uploaded successfully!")
                        print(f"🔗 Public URL: {profile_image_url}")
                        
                    except Exception as storage_error:
                        print(f"❌ Storage upload failed: {storage_error}")
                        import traceback
                        traceback.print_exc()
                        # Continue without image
                        
                except Exception as e:
                    print(f"⚠️ Error processing image: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        # Extract allowed fields (these MUST be saved to database)
        update_data = {}
        allowed_fields = {
            'full_name': str,
            'bio': str,
            'session_rate_usd': float,
            'average_response_time_minutes': int,
            'specializations': list,
            'languages_spoken': list,
            'years_of_experience': int,
            'is_online': bool
        }
        
        for key, expected_type in allowed_fields.items():
            if key in data and data[key] is not None and data[key] != '':
                try:
                    value = data[key]
                    
                    if expected_type == float:
                        update_data[key] = float(value)
                    elif expected_type == int:
                        update_data[key] = int(value)
                    elif expected_type == bool:
                        update_data[key] = str(value).lower() in ('true', '1', 'yes')
                    elif expected_type == list:
                        if isinstance(value, list):
                            update_data[key] = value
                        elif isinstance(value, str):
                            try:
                                update_data[key] = json.loads(value)
                            except:
                                # Try splitting by comma
                                update_data[key] = [v.strip() for v in value.split(',') if v.strip()]
                    else:
                        update_data[key] = value
                        
                    print(f"  ✓ {key}: {update_data[key]}")
                except Exception as e:
                    print(f"⚠️ Error converting {key}={value}: {str(e)}")
        
        # Add profile image URL if successfully uploaded
        if profile_image_url:
            update_data['profile_image_url'] = profile_image_url
            print(f"  ✓ profile_image_url: {profile_image_url}")
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        print(f"📊 Saving to database: {list(update_data.keys())}")
        
        # Update profile in Supabase - ADD updated_at timestamp
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table('psychologist_profiles')\
            .update(update_data)\
            .eq('user_id', user_id)\
            .execute()
        
        if response.data:
            print(f"✅ Profile updated successfully")
            saved_profile = response.data[0]
            print(f"✅ Saved fields: {list(saved_profile.keys())}")
            if 'profile_image_url' in saved_profile:
                print(f"✅ Profile image URL in response: {saved_profile['profile_image_url']}")
            else:
                print(f"⚠️ WARNING: profile_image_url NOT in saved profile!")
                print(f"⚠️ Full response: {saved_profile}")
            return jsonify(saved_profile), 200
        else:
            print(f"❌ No data in response: {response}")
            return jsonify({"error": "Failed to update profile"}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error in update_profile: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/online-status', methods=['PUT'])
@require_auth
@require_psychologist_role
def update_online_status(psychologist_service, emotion_detector, user_id: str):
    """Toggle psychologist online/offline status"""
    try:
        data = request.get_json()
        is_online = data.get('is_online', False)
        
        profile = run_async(
            psychologist_service.toggle_psychologist_online_status(user_id, is_online)
        )
        
        return jsonify(profile), 200
    except Exception as e:
        print(f"Error updating online status: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PSYCHOLOGIST SEARCH & DISCOVERY ENDPOINTS
# ============================================================================

@psychologist_bp.route('/search', methods=['GET'])
@require_auth
def search_psychologists(psychologist_service, emotion_detector, user_id: str):
    """Search for psychologists with filters"""
    try:
        # Get query parameters
        specializations = request.args.getlist('specializations')
        languages = request.args.getlist('languages')
        min_rating = request.args.get('min_rating', type=float)
        is_online_only = request.args.get('is_online_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        loop = asyncio.get_event_loop()
        psychologists, total = loop.run_until_complete(
            psychologist_service.search_psychologists(
                specializations=specializations if specializations else None,
                languages=languages if languages else None,
                min_rating=min_rating,
                is_online_only=is_online_only,
                limit=limit,
                offset=offset
            )
        )
        
        return jsonify({
            "psychologists": psychologists,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/recommended', methods=['GET'])
def get_recommended():
    """Get recommended psychologists - NO AUTH REQUIRED"""
    try:
        from database.supabase_db import supabase
        
        print("🔍 Fetching recommended psychologists...")
        
        # First, try to get online psychologists
        response = supabase.table('psychologist_profiles').select(
            'id, user_id, full_name, bio, specializations, languages_spoken, session_rate_usd, average_response_time_minutes, profile_image_url, is_online'
        ).eq('is_online', True).execute()
        
        print(f"📊 Found {len(response.data) if response.data else 0} online psychologists")
        
        # If no online psychologists, get all psychologists
        if not response.data or len(response.data) == 0:
            print("⚠️ No online psychologists found, fetching all psychologists...")
            response = supabase.table('psychologist_profiles').select(
                'id, user_id, full_name, bio, specializations, languages_spoken, session_rate_usd, average_response_time_minutes, profile_image_url, is_online'
            ).execute()
            print(f"📊 Found {len(response.data) if response.data else 0} total psychologists")
        
        psychologists = []
        if response.data:
            for psych in response.data:
                try:
                    # Calculate average rating for this psychologist
                    ratings_response = supabase.table('psychologist_ratings').select(
                        'rating'
                    ).eq('psychologist_id', psych.get('id')).execute()
                    
                    avg_rating = 4.5
                    review_count = 0
                    if ratings_response.data and len(ratings_response.data) > 0:
                        review_count = len(ratings_response.data)
                        ratings = [r.get('rating', 4.5) for r in ratings_response.data]
                        avg_rating = sum(ratings) / len(ratings) if ratings else 4.5
                    
                    psychologists.append({
                        'id': str(psych.get('id')),
                        'user_id': str(psych.get('user_id')),
                        'full_name': psych.get('full_name', 'Psychology Student'),
                        'bio': psych.get('bio', 'Available for support'),
                        'specializations': psych.get('specializations', []),
                        'languages_spoken': psych.get('languages_spoken', ['English']),
                        'session_rate_usd': psych.get('session_rate_usd', 0),
                        'average_response_time_minutes': psych.get('average_response_time_minutes', 5),
                        'profile_image_url': psych.get('profile_image_url'),
                        'is_online': psych.get('is_online', False),  # Include online status
                        'average_rating': round(avg_rating, 1),  # Frontend expects 'average_rating'
                        'review_count': review_count
                    })
                except Exception as psych_error:
                    print(f"⚠️ Error processing psychologist {psych.get('id')}: {str(psych_error)}")
                    continue
        
        print(f"✅ Returning {len(psychologists)} psychologists to frontend")
        return jsonify(psychologists), 200
    except Exception as e:
        import traceback
        print(f"❌ Error in get_recommended: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CHAT REQUEST ENDPOINTS
# ============================================================================

@psychologist_bp.route('/request', methods=['POST'])
def create_request():
    """Create a chat request to a psychologist"""
    try:
        from database.supabase_db import supabase
        from services.auth_service import AuthService
        
        data = request.get_json()
        psychologist_id = data.get('psychologist_id')
        message = data.get('message', '')
        urgency_level = data.get('urgency_level', 'medium')
        
        if not psychologist_id:
            return jsonify({"error": "psychologist_id required"}), 400
        
        # Get user ID from JWT token (preferred) or fallback to body for development
        auth_header = request.headers.get('Authorization', '')
        user_id = None
        
        if auth_header.startswith('Bearer '):
            try:
                access_token = auth_header.split(' ')[1]
                print(f"🔐 Verifying JWT token...")
                auth_result = AuthService.verify_token(access_token)
                
                if not auth_result['success']:
                    print(f"❌ Token verification failed: {auth_result.get('error')}")
                    return jsonify({"error": "Invalid token"}), 401
                
                user_id = auth_result['user'].id
                print(f"✅ User verified via JWT: {user_id}")
            except Exception as e:
                print(f"⚠️ Token verification error: {str(e)}")
                # Fall back to user_id from body for testing
                user_id = data.get('user_id')
                if not user_id:
                    return jsonify({"error": "Authentication failed and no user_id provided"}), 401
                print(f"⚠️ Using user_id from request body: {user_id}")
        else:
            # Development mode: accept user_id from body
            user_id = data.get('user_id')
            if not user_id:
                print("❌ No Authorization header and no user_id in body")
                return jsonify({"error": "Authentication required (Authorization header or user_id)"}), 401
            print(f"⚠️ Development mode: using user_id from body: {user_id}")
        
        # Verify psychologist exists
        psych_response = supabase.table('psychologist_profiles').select('id').eq('id', psychologist_id).execute()
        if not psych_response.data:
            return jsonify({"error": "Psychologist not found"}), 404
        
        # Get the chat_session_id from request (to link psychologist to user's original chat)
        chat_session_id = data.get('chat_session_id')
        
        # Create chat request
        request_data = {
            'user_id': user_id,
            'psychologist_id': psychologist_id,
            'message': message,
            'urgency_level': urgency_level,
            'status': 'pending'
        }
        
        # If user was in a chat session, link it
        if chat_session_id:
            request_data['chat_session_id'] = chat_session_id
            print(f"📎 Linking to original chat session: {chat_session_id}")
        
        print(f"📝 Creating chat request: user={user_id}, psych={psychologist_id}")
        response = supabase.table('psychologist_chat_requests').insert(request_data).execute()
        
        if response.data:
            print(f"✅ Chat request created: {response.data[0].get('id')}")
            return jsonify({
                'request_id': str(response.data[0].get('id')),
                'status': 'pending',
                'message': 'Request sent successfully'
            }), 201
        else:
            return jsonify({"error": "Failed to create request"}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error in create_request: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/requests/pending', methods=['GET'])
def get_pending_requests():
    """Get pending chat requests for psychologist"""
    try:
        from database.supabase_db import supabase
        
        # Get user_id from header
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        print(f"📋 Fetching pending requests for user: {user_id}")
        
        # First, get the psychologist profile to find the psychologist_id
        profile_response = supabase.table('psychologist_profiles')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not profile_response.data:
            print(f"⚠️ No psychologist profile found for user {user_id}")
            return jsonify({"requests": [], "count": 0}), 200
        
        psychologist_id = profile_response.data[0].get('id')
        print(f"📋 Found psychologist_id: {psychologist_id}")
        
        print(f"📋 Fetching pending requests for psychologist: {psychologist_id}")
        
        # Get all pending requests for this psychologist
        response = supabase.table('psychologist_chat_requests')\
            .select('*')\
            .eq('psychologist_id', psychologist_id)\
            .eq('status', 'pending')\
            .order('created_at', desc=True)\
            .execute()
        
        requests_list = response.data or []
        print(f"✅ Found {len(requests_list)} pending requests")
        
        # DEBUG: Show all requests if none found
        if len(requests_list) == 0:
            all_requests = supabase.table('psychologist_chat_requests')\
                .select('psychologist_id, status')\
                .eq('status', 'pending')\
                .execute()
            print(f"🔍 DEBUG: Total pending requests in DB: {len(all_requests.data or [])}")
            if all_requests.data:
                psych_ids = set(r.get('psychologist_id') for r in all_requests.data)
                print(f"🔍 DEBUG: Pending requests for psychologist IDs: {psych_ids}")
                print(f"🔍 DEBUG: Looking for: {psychologist_id}")
        
        # Get user emails for all requests
        formatted_requests = []
        for req in requests_list:
            request_user_id = req.get('user_id')
            user_name = 'Anonymous User'
            
            # Try to get user name from users table
            try:
                user_response = supabase.table('users')\
                    .select('full_name, email')\
                    .eq('id', request_user_id)\
                    .limit(1)\
                    .execute()
                
                if user_response.data:
                    user_full_name = user_response.data[0].get('full_name')
                    user_email = user_response.data[0].get('email', '')
                    # Use full_name if available, otherwise fallback to email username
                    user_name = user_full_name if user_full_name else (user_email.split('@')[0] if user_email else 'Anonymous User')
            except Exception as e:
                print(f"⚠️ Could not fetch user info for {request_user_id}: {str(e)}")
            
            formatted_requests.append({
                'id': req.get('id'),
                'user_id': req.get('user_id'),
                'user_name': user_name,
                'message': req.get('message'),
                'urgency_level': req.get('urgency_level'),
                'status': req.get('status'),
                'created_at': req.get('created_at'),
                'responded_at': req.get('responded_at')
            })
        
        return jsonify({
            'requests': formatted_requests,
            'count': len(formatted_requests)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error in get_pending_requests: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/request/<request_id>/accept', methods=['POST'])
def accept_request(request_id: str):
    """Accept a chat request and create session"""
    try:
        from database.supabase_db import supabase
        from datetime import datetime
        import uuid
        
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            data = request.get_json() or {}
            user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        print(f"✅ Accepting request {request_id} by psychologist {user_id}")
        
        # Get the request
        req_response = supabase.table('psychologist_chat_requests')\
            .select('*')\
            .eq('id', request_id)\
            .limit(1)\
            .execute()
        
        if not req_response.data:
            return jsonify({"error": "Request not found"}), 404
        
        chat_request = req_response.data[0]
        chat_session_id = chat_request.get('chat_session_id')
        
        if not chat_session_id:
            return jsonify({"error": "No chat session linked to this request"}), 400
        
        print(f"📎 Psychologist joining chat session: {chat_session_id}")
        
        # Update request status to accepted
        supabase.table('psychologist_chat_requests')\
            .update({
                'status': 'accepted',
                'responded_at': datetime.utcnow().isoformat()
            })\
            .eq('id', request_id)\
            .execute()
        
        # Get psychologist profile to get psychologist_id (UUID)
        psych_profile = supabase.table('psychologist_profiles')\
            .select('id')\
            .eq('user_id', user_id)\
            .single()\
            .execute()
        
        if not psych_profile.data:
            return jsonify({"error": "Psychologist profile not found"}), 404
        
        psychologist_id = psych_profile.data['id']
        
        # JOIN the original chat session by adding psychologist to it
        supabase.table('chat_sessions')\
            .update({
                'psychologist_id': psychologist_id,
                'psychologist_joined_at': datetime.utcnow().isoformat(),
                'has_psychologist': True
            })\
            .eq('id', chat_session_id)\
            .execute()
        
        # Add a system message to the chat
        supabase.table('session_messages')\
            .insert({
                'session_id': chat_session_id,
                'user_id': chat_request.get('user_id'),
                'role': 'system',
                'content': '🧑‍⚕️ A psychologist has joined the conversation.',
                'created_at': datetime.utcnow().isoformat()
            })\
            .execute()
        
        # Create a psychologist_session record for tracking (optional, for psychologist dashboard)
        session_data = {
            'request_id': request_id,
            'user_id': chat_request.get('user_id'),
            'psychologist_id': psychologist_id,
            'chat_session_id': chat_session_id,
            'title': f"Session with {chat_request.get('user_id', 'User')[:8]}",
            'started_at': datetime.utcnow().isoformat(),
            'message_count': 0
        }
        
        session_response = supabase.table('psychologist_sessions')\
            .insert(session_data)\
            .execute()
        
        if session_response.data:
            print(f"✅ Psychologist joined chat session: {chat_session_id}")
            return jsonify({
                "success": True,
                "chat_session_id": chat_session_id,
                "psychologist_session_id": session_response.data[0].get('id')
            }), 200
        else:
            return jsonify({"error": "Failed to create session"}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error in accept_request: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/requests/<request_id>/accept', methods=['POST'])
def accept_request_alt(request_id: str):
    """Compatibility wrapper: accept endpoint with plural 'requests' in path."""
    print(f"🔁 Redirecting plural accept route for {request_id} to canonical accept endpoint")
    return accept_request(request_id)


@psychologist_bp.route('/request/<request_id>/reject', methods=['POST'])
def reject_request(request_id: str):
    """Reject a chat request"""
    try:
        from database.supabase_db import supabase
        from datetime import datetime
        
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            data = request.get_json() or {}
            user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        print(f"❌ Rejecting request {request_id} with reason: {reason}")
        
        # Update request status to rejected
        response = supabase.table('psychologist_chat_requests')\
            .update({
                'status': 'rejected',
                'responded_at': datetime.utcnow().isoformat(),
                'response_note': reason
            })\
            .eq('id', request_id)\
            .execute()
        
        if response.data:
            print(f"✅ Request rejected")
            return jsonify({
                "success": True,
                "request": response.data[0]
            }), 200
        else:
            return jsonify({"error": "Failed to reject request"}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error in reject_request: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/requests/<request_id>/reject', methods=['POST'])
def reject_request_alt(request_id: str):
    """Compatibility wrapper: reject endpoint with plural 'requests' in path."""
    print(f"🔁 Redirecting plural reject route for {request_id} to canonical reject endpoint")
    return reject_request(request_id)


# ============================================================================
# SESSION MESSAGE ENDPOINTS
# ============================================================================

@psychologist_bp.route('/session/<session_id>/message', methods=['POST'])
@require_auth
def send_message(psychologist_service, emotion_detector, user_id: str, session_id: str):
    """Send a message in a session"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({"error": "Message content required"}), 400
        
        loop = asyncio.get_event_loop()
        message = loop.run_until_complete(
            psychologist_service.send_session_message(session_id, user_id, content)
        )
        
        return jsonify(message), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/session/<session_id>/messages', methods=['GET'])
@require_auth
def get_messages(psychologist_service, emotion_detector, user_id: str, session_id: str):
    """Get messages from a session"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        loop = asyncio.get_event_loop()
        messages = loop.run_until_complete(
            psychologist_service.get_session_messages(session_id, limit, offset)
        )
        
        return jsonify({"messages": messages}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/<session_id>/messages', methods=['GET'])
def get_messages_plural(session_id: str):
    """Get messages from a session - plural route for compatibility"""
    try:
        from database.supabase_db import supabase
        
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        print(f"📨 Fetching messages for session: {session_id}")
        
        # Get messages from the session
        response = supabase.table('psychologist_session_messages')\
            .select('*')\
            .eq('session_id', session_id)\
            .order('created_at', desc=False)\
            .limit(limit)\
            .execute()
        
        messages = response.data or []
        print(f"✅ Found {len(messages)} messages")
        
        return jsonify({"messages": messages}), 200
    except Exception as e:
        import traceback
        print(f"❌ Error in get_messages_plural: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/message/<message_id>/read', methods=['PUT'])
@require_auth
def mark_read(psychologist_service, emotion_detector, user_id: str, message_id: str):
    """Mark message as read"""
    try:
        loop = asyncio.get_event_loop()
        message = loop.run_until_complete(
            psychologist_service.mark_message_as_read(message_id)
        )
        
        return jsonify(message), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@psychologist_bp.route('/session/<session_id>/end', methods=['POST'])
@require_auth
@require_psychologist_role
def end_session(psychologist_service, emotion_detector, user_id: str, session_id: str):
    """End a psychologist session"""
    try:
        data = request.get_json() or {}
        
        loop = asyncio.get_event_loop()
        session = loop.run_until_complete(
            psychologist_service.end_psychologist_session(
                session_id,
                session_notes=data.get('session_notes'),
                follow_up_required=data.get('follow_up_required', False),
                follow_up_date=data.get('follow_up_date')
            )
        )
        
        return jsonify(session), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/active', methods=['GET'])
@require_auth
def get_user_active_sessions(psychologist_service, emotion_detector, user_id: str):
    """Get active sessions for user"""
    try:
        sessions = run_async(
            psychologist_service.get_user_active_sessions(user_id)
        )
        
        print(f"🔍 User {user_id} active sessions: {len(sessions)} found")
        
        return jsonify({"active_sessions": sessions}), 200
    except Exception as e:
        import traceback
        print(f"❌ Error in get_user_active_sessions: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/psychologist/active', methods=['GET'])
@require_auth
@require_psychologist_role
def get_psychologist_active_sessions(psychologist_service, emotion_detector, user_id: str):
    """Get active sessions for psychologist"""
    try:
        sessions = run_async(
            psychologist_service.get_psychologist_active_sessions(user_id)
        )
        
        response = jsonify({"sessions": sessions})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        import traceback
        print(f"❌ Error in get_psychologist_active_sessions: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/completed', methods=['GET'])
@require_auth
@require_psychologist_role
def get_psychologist_completed_sessions(psychologist_service, emotion_detector, user_id: str):
    """Get completed sessions for psychologist"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sessions = loop.run_until_complete(
                psychologist_service.get_psychologist_completed_sessions(user_id, limit)
            )
        finally:
            loop.close()
        
        return jsonify({"sessions": sessions}), 200
    except Exception as e:
        print(f"❌ Error in get_psychologist_completed_sessions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/ratings', methods=['GET'])
@require_auth
@require_psychologist_role
def get_psychologist_ratings(psychologist_service, emotion_detector, user_id: str):
    """Get ratings and reviews for psychologist"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            ratings = loop.run_until_complete(
                psychologist_service.get_psychologist_ratings(user_id, limit)
            )
        finally:
            loop.close()
        
        # Calculate statistics
        stats = {
            "average_rating": 0,
            "total_ratings": len(ratings) if ratings else 0
        }
        
        if ratings:
            avg = sum(r.get('rating', 0) for r in ratings) / len(ratings)
            stats["average_rating"] = round(avg, 2)
        
        return jsonify({
            "ratings": ratings,
            "stats": stats
        }), 200
    except Exception as e:
        print(f"❌ Error in get_psychologist_ratings: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/requests/<request_id>', methods=['GET'])
def get_request_detail(request_id: str):
    """Get details of a specific chat request"""
    try:
        from database.supabase_db import supabase
        
        print(f"📋 Fetching request details for: {request_id}")
        
        # Get request details
        response = supabase.table('psychologist_chat_requests')\
            .select('*')\
            .eq('id', request_id)\
            .limit(1)\
            .execute()
        
        if not response.data:
            print(f"❌ Request not found: {request_id}")
            return jsonify({"error": "Request not found"}), 404
        
        request_data = response.data[0]
        request_user_id = request_data.get('user_id')
        
        print(f"📋 Request user_id: {request_user_id}")
        
        # Try to get user name, but don't fail if we can't
        user_name = 'User'
        try:
            # First try public.users by id
            user_response = supabase.table('users')\
                .select('email, username')\
                .eq('id', request_user_id)\
                .limit(1)\
                .execute()

            print(f"📋 User query response (by id): {user_response.data}")

            if user_response.data and len(user_response.data) > 0:
                user_row = user_response.data[0]
                user_email = user_row.get('email', '')
                user_un = user_row.get('username') or ''
                if user_un:
                    user_name = user_un
                elif user_email:
                    user_name = user_email.split('@')[0]
                print(f"✅ Got user name: {user_name}")
            else:
                # As a fallback, try to search users table by email or username fields containing the id (if a mismatch)
                fallback_resp = supabase.table('users')\
                    .select('email, username')\
                    .ilike('email', f"%{request_user_id}%")\
                    .limit(1)\
                    .execute()
                print(f"📋 User fallback response: {fallback_resp.data}")
                if fallback_resp.data:
                    fr = fallback_resp.data[0]
                    user_name = fr.get('username') or fr.get('email', '').split('@')[0] or 'User'
                    print(f"✅ Got user name from fallback: {user_name}")
                else:
                    print(f"⚠️ No user found with ID {request_user_id} in public.users")
        except Exception as user_err:
            print(f"⚠️ Could not fetch user email: {str(user_err)}")
            import traceback
            traceback.print_exc()
        
        # Format response
        formatted_request = {
            'id': request_data.get('id'),
            'user_id': request_user_id,
            'user_name': user_name,
            'message': request_data.get('message'),
            'urgency_level': request_data.get('urgency_level'),
            'status': request_data.get('status'),
            'created_at': request_data.get('created_at'),
            'responded_at': request_data.get('responded_at')
        }
        
        print(f"✅ Request details retrieved for {user_name}")
        return jsonify({"request": formatted_request}), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error in get_request_detail: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/<session_id>/messages', methods=['POST'])
@require_auth
def send_session_message(psychologist_service, emotion_detector, user_id: str, session_id: str):
    """Send a message in a session"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({"error": "Message content required"}), 400
        
        message = run_async(
            psychologist_service.send_session_message(session_id, user_id, content)
        )
        
        return jsonify({"success": True, "message": message}), 201
            
    except Exception as e:
        import traceback
        print(f"❌ Error in send_session_message: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/sessions/<session_id>/end', methods=['POST'])
@require_auth
def end_psychologist_session(psychologist_service, emotion_detector, user_id: str, session_id: str):
    """End a psychologist session"""
    try:
        from database.supabase_db import supabase
        from datetime import datetime
        
        data = request.get_json() or {}
        session_notes = data.get('session_notes', '')
        
        print(f"🔚 Ending psychologist session: {session_id}")
        
        # Get the session to find the chat_session_id
        session_response = supabase.table('psychologist_sessions').select(
            'id, chat_session_id, started_at'
        ).eq('id', session_id).single().execute()
        
        if not session_response.data:
            return jsonify({"error": "Session not found"}), 404
        
        session = session_response.data
        chat_session_id = session.get('chat_session_id')
        started_at = session.get('started_at')
        
        # Calculate duration
        duration_minutes = 0
        if started_at:
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end_time = datetime.utcnow()
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
        
        # End the psychologist session
        supabase.table('psychologist_sessions').update({
            'ended_at': datetime.utcnow().isoformat(),
            'duration_minutes': duration_minutes,
            'session_notes': session_notes
        }).eq('id', session_id).execute()
        
        # Remove psychologist from the chat session
        if chat_session_id:
            supabase.table('chat_sessions').update({
                'has_psychologist': False
            }).eq('id', chat_session_id).execute()
            
            # Add a system message
            supabase.table('session_messages').insert({
                'session_id': chat_session_id,
                'user_id': user_id,
                'role': 'system',
                'content': '🧑‍⚕️ The psychologist has left the conversation.',
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        
        print(f"✅ Session ended: {session_id}")
        return jsonify({"success": True, "message": "Session ended"}), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error ending session: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# RATING & REVIEW ENDPOINTS
# ============================================================================

@psychologist_bp.route('/rating', methods=['POST'])
@require_auth
def create_rating(psychologist_service, emotion_detector, user_id: str):
    """Create a rating for a psychologist"""
    try:
        data = request.get_json()
        psychologist_id = data.get('psychologist_id')
        rating = data.get('rating')
        
        if not psychologist_id or rating is None:
            return jsonify({"error": "Missing required fields"}), 400
        
        try:
            rating = float(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid rating value"}), 400
        
        loop = asyncio.get_event_loop()
        rating_obj = loop.run_until_complete(
            psychologist_service.create_rating(
                psychologist_id=psychologist_id,
                user_id=user_id,
                rating=rating,
                review_text=data.get('review_text'),
                session_id=data.get('session_id')
            )
        )
        
        return jsonify(rating_obj), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/psychologist/<psychologist_id>/reviews', methods=['GET'])
@require_auth
def get_reviews(psychologist_service, emotion_detector, user_id: str, psychologist_id: str):
    """Get reviews for a psychologist"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        loop = asyncio.get_event_loop()
        reviews = loop.run_until_complete(
            psychologist_service.get_psychologist_reviews(psychologist_id, limit)
        )
        
        return jsonify({"reviews": reviews}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@psychologist_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications(psychologist_service, emotion_detector, user_id: str):
    """Get user notifications"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        loop = asyncio.get_event_loop()
        notifications = loop.run_until_complete(
            psychologist_service.get_user_notifications(user_id, unread_only, limit)
        )
        
        return jsonify({"notifications": notifications}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@psychologist_bp.route('/notification/<notification_id>/read', methods=['PUT'])
@require_auth
def mark_notification_read(psychologist_service, emotion_detector, user_id: str, notification_id: str):
    """Mark notification as read"""
    try:
        loop = asyncio.get_event_loop()
        notification = loop.run_until_complete(
            psychologist_service.mark_notification_as_read(notification_id)
        )
        
        return jsonify(notification), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# EMOTION ANALYSIS & RECOMMENDATION ENDPOINT
# ============================================================================

@psychologist_bp.route('/analyze-emotion', methods=['POST'])
@require_auth
def analyze_emotion(psychologist_service, emotion_detector, user_id):
    """Analyze message emotion/urgency for logged-in users (JWT required)."""
    try:
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()

        if not message:
            return jsonify({"error": "Message required"}), 400

        from services.emotion_analyzer import EmotionDetector

        analysis = EmotionDetector.analyze_message(message)
        detected = analysis.get('detected_emotions') or []
        emotion = detected[0] if detected else 'neutral'
        urgency_level = analysis.get('urgency_level', 'low')
        is_positive = analysis.get('is_positive', False)

        # Auto-suggest student modal only for high urgency, non-positive messages
        suggest_student_support = (
            urgency_level == 'high' and not is_positive
        )

        print(
            f"📊 Emotion analysis user={user_id} "
            f"emotion={emotion} urgency={urgency_level} "
            f"suggest_student={suggest_student_support}"
        )

        return jsonify({
            "emotion": emotion,
            "urgency_level": urgency_level,
            "suggest_student_support": suggest_student_support,
            "detected_emotions": detected,
        }), 200
    except Exception as e:
        import traceback
        print(f"❌ Error in analyze-emotion endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@psychologist_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200
