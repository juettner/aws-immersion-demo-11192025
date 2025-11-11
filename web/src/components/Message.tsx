import React from 'react';
import './Message.css';

export interface MessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: unknown;
  visualization?: string;
  status?: 'sending' | 'sent' | 'error';
}

const Message: React.FC<MessageProps> = ({
  role,
  content,
  timestamp,
  data,
  visualization,
  status = 'sent',
}) => {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderDataTable = (tableData: unknown): React.ReactNode => {
    if (!tableData || typeof tableData !== 'object') return null;
    
    if (Array.isArray(tableData) && tableData.length > 0) {
      const headers = Object.keys(tableData[0]);
      return (
        <div className="message-data-table">
          <table>
            <thead>
              <tr>
                {headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, idx) => (
                <tr key={idx}>
                  {headers.map((header) => (
                    <td key={header}>{String(row[header])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    
    return (
      <div className="message-data-json">
        <pre>{JSON.stringify(tableData, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className={`message message-${role} message-${status}`}>
      <div className="message-header">
        <span className="message-role">
          {role === 'user' ? 'You' : 'AI Assistant'}
        </span>
        <span className="message-timestamp">{formatTime(timestamp)}</span>
      </div>
      
      <div className="message-content">
        <p>{content}</p>
        
        {data ? renderDataTable(data) : null}
        
        {visualization && (
          <div className="message-visualization">
            <img 
              src={visualization} 
              alt="Data visualization" 
              className="visualization-image"
            />
          </div>
        )}
      </div>
      
      {status === 'sending' && (
        <div className="message-status">Sending...</div>
      )}
      {status === 'error' && (
        <div className="message-status error">Failed to send</div>
      )}
    </div>
  );
};

export default Message;
