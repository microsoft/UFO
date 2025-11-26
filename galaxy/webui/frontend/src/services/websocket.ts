// WebSocket client for connecting to Galaxy backend
export interface GalaxyEvent {
  event_type?: string;
  type?: string; // For non-event messages like reset_acknowledged
  timestamp: number;
  source_id?: string;
  data?: any;
  // Task events
  task_id?: string;
  status?: string;
  result?: any;
  error?: string | null;
  // Constellation events
  constellation_id?: string;
  constellation_state?: string;
  new_ready_tasks?: string[];
  // Agent events
  agent_name?: string;
  agent_type?: string;
  output_type?: string;
  output_data?: any;
  // Device events
  device_id?: string;
  device_status?: string;
  device_info?: any;
  all_devices?: Record<string, any>;
  // Session control messages
  message?: string;
  session_name?: string;
  task_name?: string;
}

export type EventCallback = (event: GalaxyEvent) => void;
export type StatusCallback = (status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting') => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventCallbacks: Set<EventCallback> = new Set();
  private isIntentionalClose = false;
  private statusCallbacks: Set<StatusCallback> = new Set();

  constructor(url?: string) {
    // Auto-detect WebSocket URL based on current location
    if (!url) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      this.url = `${protocol}//${host}/ws`;
    } else {
      this.url = url;
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.notifyStatus('connecting');
        this.ws = new WebSocket(this.url);
        this.isIntentionalClose = false;

        this.ws.onopen = () => {
          console.log('🌌 Connected to Galaxy WebSocket');
          this.reconnectAttempts = 0;
           this.notifyStatus('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            console.log('📨 Raw WebSocket message received:', event.data);
            const data: GalaxyEvent = JSON.parse(event.data);
            console.log('📦 Parsed event data:', data);
            console.log('🔔 Notifying', this.eventCallbacks.size, 'callbacks');
            this.notifyCallbacks(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.notifyStatus('disconnected');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket connection closed');
          this.notifyStatus('disconnected');
          if (!this.isIntentionalClose) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    this.notifyStatus('reconnecting');
    
    setTimeout(() => {
      this.connect().catch(() => {
        // Reconnect will be attempted again by onclose handler
      });
    }, delay);
  }

  disconnect() {
    this.isIntentionalClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.notifyStatus('disconnected');
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  sendRequest(request: string) {
    this.send({
      type: 'request',
      text: request,
      timestamp: Date.now(),
    });
  }

  sendReset() {
    this.send({
      type: 'reset',
      timestamp: Date.now(),
    });
  }

  sendPing() {
    this.send({
      type: 'ping',
      timestamp: Date.now(),
    });
  }

  onEvent(callback: EventCallback) {
    this.eventCallbacks.add(callback);
    return () => {
      this.eventCallbacks.delete(callback);
    };
  }

  onStatusChange(callback: StatusCallback) {
    this.statusCallbacks.add(callback);
    return () => {
      this.statusCallbacks.delete(callback);
    };
  }

  private notifyCallbacks(event: GalaxyEvent) {
    console.log('🎯 notifyCallbacks called with event:', event.event_type);
    console.log('📋 Number of registered callbacks:', this.eventCallbacks.size);
    let callbackIndex = 0;
    this.eventCallbacks.forEach((callback) => {
      callbackIndex++;
      try {
        console.log(`🔄 Executing callback ${callbackIndex}/${this.eventCallbacks.size}`);
        callback(event);
        console.log(`✅ Callback ${callbackIndex} executed successfully`);
      } catch (error) {
        console.error('Error in event callback:', error);
      }
    });
  }

  private notifyStatus(status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting') {
    this.statusCallbacks.forEach((callback) => {
      try {
        callback(status);
      } catch (error) {
        console.error('Error in status callback:', error);
      }
    });
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let wsClientInstance: WebSocketClient | null = null;

export function getWebSocketClient(): WebSocketClient {
  if (!wsClientInstance) {
    wsClientInstance = new WebSocketClient();
  }
  return wsClientInstance;
}
