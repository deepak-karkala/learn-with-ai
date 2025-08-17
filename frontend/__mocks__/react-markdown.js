import React from 'react';

// Mock react-markdown to render as a simple div with the children
const ReactMarkdown = ({ children, ...props }) => {
  return React.createElement('div', { ...props, 'data-testid': 'markdown-content' }, children);
};

module.exports = ReactMarkdown;
module.exports.default = ReactMarkdown;