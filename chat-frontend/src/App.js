import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [tools, setTools] = useState([]);
  const [servers, setServers] = useState([]);
  const [authWindow, setAuthWindow] = useState(null);

  // Fetch servers and tools on mount
  useEffect(() => {
    fetchServers();
    fetchTools();
  }, []);

  // Poll for server status changes (after auth)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchServers();
      fetchTools();
    }, 3000); // Check every 3 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchServers = async () => {
    try {
      const res = await fetch('http://localhost:5001/api/servers');
      const data = await res.json();
      setServers(data.servers || []);
    } catch (err) {
      console.error('Error fetching servers:', err);
    }
  };

  const fetchTools = async () => {
    try {
      const res = await fetch('http://localhost:5001/api/tools');
      const data = await res.json();
      setTools(data.tools || []);
    } catch (err) {
      console.error('Error fetching tools:', err);
    }
  };

  const authenticateServer = async (serverKey) => {
    try {
      const res = await fetch(`http://localhost:5001/api/oauth/start/${serverKey}`);
      const data = await res.json();
      
      if (data.error) {
        alert(`Error: ${data.error}`);
        return;
      }

      // Open auth window
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      
      const popup = window.open(
        data.auth_url,
        'OAuth Authentication',
        `width=${width},height=${height},left=${left},top=${top}`
      );
      
      setAuthWindow(popup);

      // Poll to check if window closed
      const pollTimer = setInterval(() => {
        if (popup && popup.closed) {
          clearInterval(pollTimer);
          setAuthWindow(null);
          // Refresh servers and tools
          fetchServers();
          fetchTools();
        }
      }, 500);

    } catch (error) {
      alert(`Error starting authentication: ${error.message}`);
    }
  };

  const disconnectServer = async (serverKey) => {
    if (!window.confirm('Are you sure you want to disconnect this server?')) {
      return;
    }

    try {
      const res = await fetch(`http://localhost:5001/api/oauth/disconnect/${serverKey}`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.error) {
        alert(`Error: ${data.error}`);
      } else {
        // Refresh servers and tools
        fetchServers();
        fetchTools();
      }
    } catch (error) {
      alert(`Error disconnecting: ${error.message}`);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();
      
      if (data.error) {
        setMessages(prev => [...prev, { 
          role: 'error', 
          content: `Error: ${data.error}` 
        }]);
      } else {
        // Add assistant response
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          toolCalls: data.tool_calls || []
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: `Connection error: ${error.message}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await fetch('http://localhost:5001/api/clear', { method: 'POST' });
      setMessages([]);
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <h1>🤖 Multi-Server MCP Chat</h1>
            <p>Chat with GPT-4 connected to multiple MCP servers</p>
          </div>
          <button onClick={clearChat} className="clear-btn">
            Clear Chat
          </button>
        </div>

        {/* Servers Panel */}
        {servers.length > 0 && (
          <div className="servers-panel">
            <h3>🖥️ Connected Servers:</h3>
            <div className="servers-list">
              {servers.map((server) => (
                <div key={server.key} className="server-card">
                  <div className="server-info">
                    <span className="server-name">{server.name}</span>
                    <span className={`server-status ${server.authenticated ? 'connected' : 'disconnected'}`}>
                      {server.authenticated ? '✅ Connected' : '⚠️ Not Connected'}
                    </span>
                  </div>
                  {server.requires_auth && (
                    <div className="server-actions">
                      {server.authenticated ? (
                        <button 
                          onClick={() => disconnectServer(server.key)}
                          className="btn-disconnect"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button 
                          onClick={() => authenticateServer(server.key)}
                          className="btn-connect"
                        >
                          Connect with Google
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tools Panel */}
        {tools.length > 0 && (
          <div className="tools-panel">
            <h3>🔧 Available Tools ({tools.length}):</h3>
            <div className="tools-list">
              {tools.map((tool, idx) => (
                <div key={idx} className="tool-badge" title={tool.function.description}>
                  {tool.function.name}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>👋 Welcome!</h2>
              <p>Try asking me to:</p>
              <ul>
                <li>"What's 25 + 17?" (Calculator)</li>
                <li>"List my recent Google Drive files" (Google Drive)</li>
                <li>"Search for 'report' in my Drive" (Google Drive)</li>
                <li>"Add 42 and 8" (Calculator)</li>
              </ul>
              {servers.some(s => s.requires_auth && !s.authenticated) && (
                <p className="hint">
                  ⚠️ Don't forget to connect servers that require authentication!
                </p>
              )}
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="message-header">
                <strong>
                  {msg.role === 'user' ? '👤 You' : 
                   msg.role === 'error' ? '⚠️ Error' : 
                   '🤖 Assistant'}
                </strong>
              </div>
              <div className="message-content">
                {msg.content}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="tool-calls-container">
                    <div className="tool-calls-header">
                      <span className="tool-calls-label">Tool Calls Made:</span>
                    </div>
                    {msg.toolCalls.map((toolCall, index) => (
                      <div key={toolCall.id || index} className="tool-call-item">
                        <div className="tool-call-header">
                          <span className="tool-badge-inline">🔧 {toolCall.name}</span>
                          <span className="tool-call-number">#{index + 1}</span>
                        </div>
                        <div className="tool-call-args">
                          <strong>Input:</strong> <pre>{JSON.stringify(toolCall.args, null, 2)}</pre>
                        </div>
                        <div className="tool-call-result">
                          <strong>Output:</strong> <pre>{toolCall.result}</pre>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message message-assistant">
              <div className="message-header">
                <strong>🤖 Assistant</strong>
              </div>
              <div className="message-content typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me to calculate or search your Drive..."
            disabled={loading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={loading || !input.trim()}
            className="send-button"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
