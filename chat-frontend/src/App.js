import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [tools, setTools] = useState([]);

  // Fetch available tools on mount
  useEffect(() => {
    fetch('http://localhost:5001/api/tools')
      .then(res => res.json())
      .then(data => setTools(data.tools || []))
      .catch(err => console.error('Error fetching tools:', err));
  }, []);

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
          toolCalls: data.tool_calls || []  // Array of all tool calls
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
            <h1>🧮 MCP Calculator Chat</h1>
            <p>Chat with GPT-4 connected to your MCP server</p>
          </div>
          <button onClick={clearChat} className="clear-btn">
            Clear Chat
          </button>
        </div>

        {/* Tools Panel */}
        {tools.length > 0 && (
          <div className="tools-panel">
            <h3>🔧 Available Tools:</h3>
            <div className="tools-list">
              {tools.map((tool, idx) => (
                <div key={idx} className="tool-badge">
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
                <li>"What's 25 + 17?"</li>
                <li>"Add 42 and 8"</li>
                <li>"Calculate the sum of 100 and 250"</li>
              </ul>
              <p className="hint">The AI will use the MCP server's <code>sum</code> tool automatically!</p>
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
                          <strong>Input:</strong> {JSON.stringify(toolCall.args, null, 2)}
                        </div>
                        <div className="tool-call-result">
                          <strong>Output:</strong> {toolCall.result}
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
            placeholder="Ask me to calculate something..."
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

