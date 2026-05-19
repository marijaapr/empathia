"""
Supabase Realtime Handler
Manages WebSocket connections for real-time features
"""

import json
import asyncio
from typing import Callable, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RealtimeHandler:
    """Handler for Supabase realtime subscriptions"""

    def __init__(self, supabase_client):
        """
        Initialize realtime handler
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self.subscriptions: Dict[str, any] = {}
        self.callbacks: Dict[str, List[Callable]] = {}

    # ========== MESSAGE SUBSCRIPTIONS ==========

    async def subscribe_to_session_messages(
        self,
        session_id: str,
        on_message: Callable
    ) -> str:
        """
        Subscribe to messages in a session (realtime updates)
        
        Args:
            session_id: UUID of the session
            on_message: Callback function for new messages
            
        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"session_messages_{session_id}"
            
            # Register callback
            if subscription_id not in self.callbacks:
                self.callbacks[subscription_id] = []
            self.callbacks[subscription_id].append(on_message)
            
            # Subscribe to changes
            subscription = self.supabase.realtime.on(
                event="*",
                schema="public",
                table="psychologist_session_messages",
                callback=self._create_message_handler(subscription_id)
            ).subscribe(self.supabase.realtime.channel_name)
            
            self.subscriptions[subscription_id] = subscription
            
            logger.info(f"Subscribed to session messages: {session_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"Error subscribing to session messages: {str(e)}")
            raise

    async def subscribe_to_notifications(
        self,
        user_id: str,
        on_notification: Callable
    ) -> str:
        """
        Subscribe to user notifications (realtime updates)
        
        Args:
            user_id: UUID of the user
            on_notification: Callback function for new notifications
            
        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"notifications_{user_id}"
            
            # Register callback
            if subscription_id not in self.callbacks:
                self.callbacks[subscription_id] = []
            self.callbacks[subscription_id].append(on_notification)
            
            # Subscribe to changes
            subscription = self.supabase.realtime.on(
                event="*",
                schema="public",
                table="notifications",
                callback=self._create_notification_handler(subscription_id, user_id)
            ).subscribe(self.supabase.realtime.channel_name)
            
            self.subscriptions[subscription_id] = subscription
            
            logger.info(f"Subscribed to notifications: {user_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"Error subscribing to notifications: {str(e)}")
            raise

    async def subscribe_to_psychologist_requests(
        self,
        psychologist_id: str,
        on_request: Callable
    ) -> str:
        """
        Subscribe to incoming chat requests for a psychologist
        
        Args:
            psychologist_id: UUID of the psychologist
            on_request: Callback function for new requests
            
        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"psychologist_requests_{psychologist_id}"
            
            # Register callback
            if subscription_id not in self.callbacks:
                self.callbacks[subscription_id] = []
            self.callbacks[subscription_id].append(on_request)
            
            # Subscribe to changes
            subscription = self.supabase.realtime.on(
                event="*",
                schema="public",
                table="psychologist_chat_requests",
                callback=self._create_request_handler(subscription_id, psychologist_id)
            ).subscribe(self.supabase.realtime.channel_name)
            
            self.subscriptions[subscription_id] = subscription
            
            logger.info(f"Subscribed to psychologist requests: {psychologist_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"Error subscribing to requests: {str(e)}")
            raise

    async def subscribe_to_online_status(
        self,
        psychologist_id: str,
        on_status_change: Callable
    ) -> str:
        """
        Subscribe to psychologist online status changes
        
        Args:
            psychologist_id: UUID of the psychologist
            on_status_change: Callback function for status changes
            
        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"online_status_{psychologist_id}"
            
            # Register callback
            if subscription_id not in self.callbacks:
                self.callbacks[subscription_id] = []
            self.callbacks[subscription_id].append(on_status_change)
            
            # Subscribe to changes in psychologist profile
            subscription = self.supabase.realtime.on(
                event="*",
                schema="public",
                table="psychologist_profiles",
                callback=self._create_status_handler(subscription_id, psychologist_id)
            ).subscribe(self.supabase.realtime.channel_name)
            
            self.subscriptions[subscription_id] = subscription
            
            logger.info(f"Subscribed to online status: {psychologist_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"Error subscribing to online status: {str(e)}")
            raise

    # ========== HANDLERS ==========

    def _create_message_handler(self, subscription_id: str) -> Callable:
        """Create handler for message events"""
        def handler(event):
            try:
                # Filter for INSERT and UPDATE events
                if event.get("type") in ["INSERT", "UPDATE"]:
                    message_data = event.get("new")
                    
                    # Call registered callbacks
                    for callback in self.callbacks.get(subscription_id, []):
                        asyncio.create_task(callback(message_data))
                
                logger.debug(f"Message event processed: {event.get('type')}")
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
        
        return handler

    def _create_notification_handler(
        self,
        subscription_id: str,
        user_id: str
    ) -> Callable:
        """Create handler for notification events"""
        def handler(event):
            try:
                # Only process new notifications for this user
                if event.get("type") == "INSERT":
                    notification_data = event.get("new")
                    
                    # Check if notification is for this user
                    if notification_data.get("user_id") == user_id:
                        # Call registered callbacks
                        for callback in self.callbacks.get(subscription_id, []):
                            asyncio.create_task(callback(notification_data))
                
                logger.debug(f"Notification event processed: {event.get('type')}")
            except Exception as e:
                logger.error(f"Error in notification handler: {str(e)}")
        
        return handler

    def _create_request_handler(
        self,
        subscription_id: str,
        psychologist_id: str
    ) -> Callable:
        """Create handler for chat request events"""
        def handler(event):
            try:
                # Only process new requests
                if event.get("type") == "INSERT":
                    request_data = event.get("new")
                    
                    # Check if request is for this psychologist
                    if request_data.get("psychologist_id") == psychologist_id:
                        # Call registered callbacks
                        for callback in self.callbacks.get(subscription_id, []):
                            asyncio.create_task(callback(request_data))
                
                logger.debug(f"Request event processed: {event.get('type')}")
            except Exception as e:
                logger.error(f"Error in request handler: {str(e)}")
        
        return handler

    def _create_status_handler(
        self,
        subscription_id: str,
        psychologist_id: str
    ) -> Callable:
        """Create handler for online status events"""
        def handler(event):
            try:
                # Only process updates
                if event.get("type") == "UPDATE":
                    profile_data = event.get("new")
                    
                    # Check if this is the psychologist we're tracking
                    if profile_data.get("id") == psychologist_id:
                        status_change = {
                            "psychologist_id": psychologist_id,
                            "is_online": profile_data.get("is_online"),
                            "last_online_at": profile_data.get("last_online_at"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Call registered callbacks
                        for callback in self.callbacks.get(subscription_id, []):
                            asyncio.create_task(callback(status_change))
                
                logger.debug(f"Status event processed: {event.get('type')}")
            except Exception as e:
                logger.error(f"Error in status handler: {str(e)}")
        
        return handler

    # ========== UNSUBSCRIBE & CLEANUP ==========

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a subscription
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            Boolean indicating success
        """
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                subscription.unsubscribe()
                
                del self.subscriptions[subscription_id]
                if subscription_id in self.callbacks:
                    del self.callbacks[subscription_id]
                
                logger.info(f"Unsubscribed: {subscription_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error unsubscribing: {str(e)}")
            return False

    async def unsubscribe_all(self) -> bool:
        """
        Unsubscribe from all subscriptions
        
        Returns:
            Boolean indicating success
        """
        try:
            for subscription_id in list(self.subscriptions.keys()):
                await self.unsubscribe(subscription_id)
            
            logger.info("Unsubscribed from all subscriptions")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from all: {str(e)}")
            return False

    # ========== TYPING INDICATORS ==========

    async def broadcast_typing(
        self,
        session_id: str,
        user_id: str,
        is_typing: bool
    ) -> bool:
        """
        Broadcast typing indicator for a session
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the user
            is_typing: Boolean indicating typing status
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create a system message to broadcast typing status
            typing_message = {
                "session_id": session_id,
                "sender_id": user_id,
                "content": json.dumps({
                    "type": "typing",
                    "is_typing": is_typing,
                    "user_id": user_id
                }),
                "message_type": "system"
            }
            
            # Send to realtime channel
            self.supabase.realtime.broadcast(
                channel_name=f"session_{session_id}",
                event="typing",
                payload=typing_message
            )
            
            return True
        except Exception as e:
            logger.error(f"Error broadcasting typing: {str(e)}")
            return False

    # ========== UTILITIES ==========

    def get_subscription_count(self) -> int:
        """Get number of active subscriptions"""
        return len(self.subscriptions)

    def get_active_subscriptions(self) -> List[str]:
        """Get list of active subscription IDs"""
        return list(self.subscriptions.keys())

    async def close(self) -> bool:
        """Close all subscriptions and clean up"""
        try:
            await self.unsubscribe_all()
            logger.info("Realtime handler closed")
            return True
        except Exception as e:
            logger.error(f"Error closing realtime handler: {str(e)}")
            return False
