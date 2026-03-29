import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function MarkdownLoader({ content }) {

  return (

    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              style={tomorrow}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className="bg-gray-700 px-1.5 py-0.5 rounded text-sm" {...props}>
              {children}
            </code>
          );
        },
        a({ node, children, ...props }) {
          return (
            <a
              className="text-blue-400 hover:text-blue-300 underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            >
              {children}
            </a>
          );
        },
        h1({ node, children, ...props }) {
          return <h1 className="text-3xl font-extrabold text-white mb-4 mt-6 border-b border-gray-700 pb-2 flex items-center gap-2" {...props}>{children}</h1>;
        },
        h2({ node, children, ...props }) {
          return <h2 className="text-2xl font-bold text-indigo-400 mb-3 mt-5 flex items-center gap-2" {...props}>{children}</h2>;
        },
        h3({ node, children, ...props }) {
          return <h3 className="text-xl font-semibold text-purple-400 mb-2 mt-4" {...props}>{children}</h3>;
        },
        h4({ node, children, ...props }) {
          return <h4 className="text-lg font-medium text-gray-200 mb-2 mt-3" {...props}>{children}</h4>;
        },
        p({ node, children, ...props }) {
          return <p className="text-gray-300 leading-relaxed mb-4 text-base" {...props}>{children}</p>;
        },
        blockquote({ node, children, ...props }) {
          return (
            <blockquote className="border-l-4 border-indigo-500 bg-gray-800/50 pl-4 py-2 my-4 italic text-gray-400 rounded-r-md" {...props}>
              {children}
            </blockquote>
          );
        },
        table({ node, children, ...props }) {
          return (
            <div className="overflow-x-auto my-6 border border-gray-700 rounded-lg shadow-xl">
              <table className="min-w-full divide-y divide-gray-700 bg-gray-900/40" {...props}>
                {children}
              </table>
            </div>
          );
        },
        thead({ node, children, ...props }) {
          return <thead className="bg-gray-800/80" {...props}>{children}</thead>;
        },
        th({ node, children, ...props }) {
          return <th className="px-4 py-2 text-left text-xs font-semibold text-indigo-300 uppercase tracking-wider" {...props}>{children}</th>;
        },
        td({ node, children, ...props }) {
          return <td className="px-4 py-2 text-sm text-gray-300 border-t border-gray-800" {...props}>{children}</td>;
        },
        hr({ node, ...props }) {
          return <hr className="my-8 border-gray-700 border-t-2 rounded-full opacity-50" {...props} />;
        },
        ul({ node, children, ...props }) {
          return <ul className="list-disc list-inside space-y-2 mb-4 ml-2" {...props}>{children}</ul>;
        },
        li({ node, children, ...props }) {
          return <li className="text-gray-300 mb-1" {...props}>{children}</li>;
        }
      }}
    >
      {content}
    </ReactMarkdown>

  );
}