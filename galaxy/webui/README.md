# Galaxy WebUI - Development & Testing Guide

## 🚀 Quick Start

### 1. Install Frontend Dependencies

```bash
cd galaxy/webui/frontend
npm install
```

### 2. Start Development Server (with Hot Reload)

```bash
# Terminal 1: Start Vite dev server (frontend with HMR)
cd galaxy/webui/frontend
npm run dev

# Terminal 2: Start Galaxy with WebUI backend
cd ../../..
python -m galaxy --webui
```

Frontend will be available at: http://localhost:5173 (Vite dev server with proxy to backend)

### 3. Build for Production

```bash
# Build frontend
cd galaxy/webui/frontend
npm run build

# Start Galaxy with WebUI (serves built frontend)
cd ../../..
python -m galaxy --webui
```

Production UI will be available at: http://localhost:8000

---

## 📖 Usage Examples

### Launch WebUI
```bash
python -m galaxy --webui
```

### Launch WebUI with Custom Session Name
```bash
python -m galaxy --webui --session-name "my_galaxy_session"
```

### Launch WebUI with Debug Logging
```bash
python -m galaxy --webui --log-level DEBUG
```

---

## 🧪 Testing

### Backend Tests

```bash
# Test WebSocket server
pytest tests/galaxy/webui/test_websocket_server.py

# Test event serialization
pytest tests/galaxy/webui/test_event_serialization.py

# Test observer pattern
pytest tests/galaxy/webui/test_websocket_observer.py
```

### Frontend Tests

```bash
cd galaxy/webui/frontend

# Run component tests
npm test

# Build and check for errors
npm run build
```

---

## 🏗️ Architecture

### Backend (FastAPI + WebSocket)
- `server.py` - FastAPI application with WebSocket endpoint
- `websocket_observer.py` - Observer that broadcasts events to WebSocket clients
- Events flow: Galaxy → EventBus → WebSocketObserver → WebSocket clients

### Frontend (React + TypeScript + Vite)
- `src/main.tsx` - Entry point, initializes WebSocket connection
- `src/App.tsx` - Main layout with starfield animation
- `src/components/Welcome.tsx` - Welcome screen with request input
- `src/components/SessionView.tsx` - Main session view layout
- `src/components/DAGVisualization.tsx` - ReactFlow-based constellation graph
- `src/components/EventLog.tsx` - Real-time event stream display
- `src/components/AgentOutput.tsx` - Agent thoughts, plans, and actions
- `src/components/ControlPanel.tsx` - Statistics and session controls
- `src/store/galaxyStore.ts` - Zustand state management
- `src/services/websocket.ts` - WebSocket client with auto-reconnect

### Communication Protocol

**Client → Server:**
```json
{ "type": "request", "text": "Your task request" }
{ "type": "reset" }
{ "type": "ping" }
```

**Server → Client:**
```json
{
  "event_type": "agent_response",
  "timestamp": 1234567890,
  "agent_name": "ConstellationAgent",
  "output_data": { "thought": "...", "plan": "..." }
}
```

---

## 🎨 Customization

### Theme Colors (tailwind.config.js)
```javascript
colors: {
  galaxy: {
    dark: '#0a0e27',    // Background
    blue: '#00d4ff',    // Primary accent
    purple: '#7b2cbf',  // Secondary accent
    pink: '#ff006e',    // Tertiary accent
  }
}
```

### WebSocket URL
Edit `vite.config.ts` proxy settings or `src/services/websocket.ts` constructor.

---

## 🐛 Troubleshooting

### WebSocket Connection Failed
- Ensure backend is running (`python -m galaxy --webui`)
- Check firewall settings for port 8000
- Verify WebSocket URL in browser console

### Frontend Not Loading
- Run `npm install` in `galaxy/webui/frontend`
- Check for TypeScript errors: `npm run build`
- Clear browser cache

### Events Not Appearing
- Check backend logs for event publishing
- Verify observer is registered: look for "WebSocket observer registered" in logs
- Test with `/health` endpoint to check connection count

---

## 📝 Development Checklist

- [x] Backend WebSocket server with FastAPI
- [x] Event system observer for broadcasting
- [x] Frontend React application structure
- [x] WebSocket client with auto-reconnect
- [x] State management with Zustand
- [x] Welcome screen with request input
- [x] DAG visualization with ReactFlow
- [x] Event log with real-time updates
- [x] Agent output display (thoughts, plans, actions)
- [x] Control panel with statistics
- [x] Galaxy CLI integration (`--webui` flag)
- [ ] Comprehensive unit tests
- [ ] Integration tests
- [ ] E2E tests with Playwright/Cypress
- [ ] Performance optimization
- [ ] Error boundary components
- [ ] Loading states and skeletons
- [ ] Toast notifications
- [ ] Session persistence
- [ ] Export/download results

---

## 🚢 Deployment

### Docker (Future)
```dockerfile
# Dockerfile for Galaxy WebUI
FROM node:18 as frontend-build
WORKDIR /app/galaxy/webui/frontend
COPY galaxy/webui/frontend/package*.json ./
RUN npm install
COPY galaxy/webui/frontend .
RUN npm run build

FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY --from=frontend-build /app/galaxy/webui/frontend/dist /app/galaxy/webui/frontend/dist
CMD ["python", "-m", "galaxy", "--webui"]
```

### Cloud Deployment
- Ensure WebSocket support (Azure App Service, AWS ECS, etc.)
- Set environment variables for API keys
- Configure CORS for production origins
- Use HTTPS for WebSocket (wss://)

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [ReactFlow](https://reactflow.dev/)
- [Zustand](https://github.com/pmndrs/zustand)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vite](https://vitejs.dev/)
