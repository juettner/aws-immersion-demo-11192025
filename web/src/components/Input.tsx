import React from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  fullWidth = false,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const classes = ['input', error && 'input--error', fullWidth && 'input--full-width', className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={`input-wrapper ${fullWidth ? 'input-wrapper--full-width' : ''}`}>
      {label && (
        <label htmlFor={inputId} className="input__label">
          {label}
        </label>
      )}
      <input id={inputId} className={classes} {...props} />
      {error && <span className="input__error">{error}</span>}
      {helperText && !error && <span className="input__helper">{helperText}</span>}
    </div>
  );
};

export default Input;
