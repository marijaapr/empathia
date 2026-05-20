"""
Request authentication helpers — verify Supabase JWT and resolve user id.
"""

from typing import Optional, Tuple, Any

from flask import jsonify

from services.auth_service import AuthService


def get_bearer_token(headers) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1].strip()
    return token or None


def extract_user_id_from_verify_result(result: dict) -> Optional[str]:
    """Normalize user id from AuthService.verify_token result."""
    if not result.get('success'):
        return None
    if result.get('user_id'):
        return str(result['user_id'])
    user = result.get('user')
    if user is None:
        return None
    # Supabase Python SDK may return UserResponse with nested .user
    inner = getattr(user, 'user', None)
    if inner is not None and getattr(inner, 'id', None):
        return str(inner.id)
    if getattr(user, 'id', None):
        return str(user.id)
    return None


def get_authenticated_user_id(headers) -> Optional[str]:
    """
    Verify Bearer JWT via Supabase Auth and return the authenticated user id.
    Does not trust X-User-ID from the client.
    """
    token = get_bearer_token(headers)
    if not token:
        return None
    result = AuthService.verify_token(token)
    return extract_user_id_from_verify_result(result)


def require_authenticated_user(headers) -> Tuple[Optional[str], Optional[Tuple[Any, int]]]:
    """
    Returns (user_id, None) on success or (None, (response, status_code)) on failure.
    """
    user_id = get_authenticated_user_id(headers)
    if user_id:
        return user_id, None
    return None, (jsonify({'error': 'Authentication required'}), 401)
