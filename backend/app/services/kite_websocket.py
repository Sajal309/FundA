"""Kite Connect WebSocket service for real-time market data."""
import os
import json
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
from app.utils import logger

try:
    from kiteconnect import KiteTicker
    KITETICKER_AVAILABLE = True
except ImportError:
    KiteTicker = None
    KITETICKER_AVAILABLE = False
    logger.warning("KiteTicker not available. WebSocket features will be disabled.")


class KiteWebSocketManager:
    """Manages Kite Connect WebSocket connections for real-time data."""
    
    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.access_token = os.getenv("KITE_ACCESS_TOKEN")
        self.kws: Optional[KiteTicker] = None
        self.subscribed_tokens: List[int] = []
        self.callbacks: Dict[int, Callable] = {}
        self.is_connected = False
        self.lock = threading.Lock()
    
    def initialize(self) -> bool:
        """Initialize WebSocket connection."""
        if not KITETICKER_AVAILABLE:
            logger.warning("KiteTicker not available. Install kiteconnect package.")
            return False
        
        if not self.api_key or not self.access_token:
            logger.warning("Kite WebSocket: API key or access token not available")
            return False
        
        try:
            self.kws = KiteTicker(self.api_key, self.access_token)
            self._setup_callbacks()
            return True
        except Exception as e:
            logger.error(f"Error initializing Kite WebSocket: {e}")
            return False
    
    def _setup_callbacks(self):
        """Setup WebSocket event callbacks."""
        if not self.kws:
            return
        
        @self.kws.on_ticks
        def on_ticks(ws, ticks):
            """Handle tick data."""
            for tick in ticks:
                instrument_token = tick.get('instrument_token')
                if instrument_token in self.callbacks:
                    try:
                        self.callbacks[instrument_token](tick)
                    except Exception as e:
                        logger.error(f"Error in tick callback: {e}")
        
        @self.kws.on_connect
        def on_connect(ws, response):
            """Handle connection."""
            logger.info("Kite WebSocket connected")
            self.is_connected = True
        
        @self.kws.on_close
        def on_close(ws, code, reason):
            """Handle disconnection."""
            logger.warning(f"Kite WebSocket closed: {code} - {reason}")
            self.is_connected = False
        
        @self.kws.on_error
        def on_error(ws, code, reason):
            """Handle errors."""
            logger.error(f"Kite WebSocket error: {code} - {reason}")
            self.is_connected = False
    
    def subscribe(self, instrument_token: int, callback: Callable) -> bool:
        """
        Subscribe to real-time ticks for an instrument.
        
        Args:
            instrument_token: Kite instrument token
            callback: Callback function that receives tick data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.kws:
            if not self.initialize():
                return False
        
        with self.lock:
            if instrument_token not in self.subscribed_tokens:
                self.subscribed_tokens.append(instrument_token)
                self.callbacks[instrument_token] = callback
                
                if self.is_connected:
                    self.kws.subscribe([instrument_token])
                    logger.info(f"Subscribed to instrument token: {instrument_token}")
                else:
                    # Connect and subscribe
                    try:
                        self.kws.connect(threaded=True)
                        time.sleep(1)  # Wait for connection
                        if self.is_connected:
                            self.kws.subscribe([instrument_token])
                            logger.info(f"Connected and subscribed to instrument token: {instrument_token}")
                    except Exception as e:
                        logger.error(f"Error connecting WebSocket: {e}")
                        return False
            else:
                # Update callback
                self.callbacks[instrument_token] = callback
        
        return True
    
    def unsubscribe(self, instrument_token: int) -> bool:
        """Unsubscribe from an instrument."""
        if not self.kws or not self.is_connected:
            return False
        
        with self.lock:
            if instrument_token in self.subscribed_tokens:
                self.kws.unsubscribe([instrument_token])
                self.subscribed_tokens.remove(instrument_token)
                if instrument_token in self.callbacks:
                    del self.callbacks[instrument_token]
                logger.info(f"Unsubscribed from instrument token: {instrument_token}")
                return True
        
        return False
    
    def disconnect(self):
        """Disconnect WebSocket."""
        if self.kws and self.is_connected:
            try:
                self.kws.close()
                self.is_connected = False
                logger.info("Kite WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket: {e}")


# Global WebSocket manager instance
_ws_manager: Optional[KiteWebSocketManager] = None


def get_websocket_manager() -> Optional[KiteWebSocketManager]:
    """Get or create WebSocket manager instance."""
    global _ws_manager
    
    if _ws_manager is None:
        _ws_manager = KiteWebSocketManager()
        if not _ws_manager.initialize():
            return None
    
    return _ws_manager

