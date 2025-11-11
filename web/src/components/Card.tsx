import React from 'react';
import './Card.css';

export interface CardProps {
  children: React.ReactNode;
  hoverable?: boolean;
  onClick?: () => void;
  className?: string;
}

export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>;
  Body: React.FC<CardBodyProps>;
  Footer: React.FC<CardFooterProps>;
} = ({ children, hoverable = false, onClick, className = '' }) => {
  const classes = ['card', hoverable && 'card--hoverable', className].filter(Boolean).join(' ');

  return (
    <div className={classes} onClick={onClick}>
      {children}
    </div>
  );
};

const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '' }) => {
  return <div className={`card__header ${className}`}>{children}</div>;
};

const CardBody: React.FC<CardBodyProps> = ({ children, className = '' }) => {
  return <div className={`card__body ${className}`}>{children}</div>;
};

const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => {
  return <div className={`card__footer ${className}`}>{children}</div>;
};

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

export default Card;
