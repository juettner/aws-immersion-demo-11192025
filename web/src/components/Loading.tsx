import React from 'react';
import './Loading.css';

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  text?: string;
}

const Loading: React.FC<LoadingProps> = ({ size = 'md', fullScreen = false, text }) => {
  const content = (
    <div className="loading">
      <div className={`loading__spinner loading__spinner--${size}`} />
      {text && <p className="loading__text">{text}</p>}
    </div>
  );

  if (fullScreen) {
    return <div className="loading--fullscreen">{content}</div>;
  }

  return content;
};

export default Loading;
