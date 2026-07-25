import type { Message } from '../types';

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} my-3`}>
      <div className={`flex max-w-3xl items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold shadow-md ${
            isUser
              ? 'bg-gradient-to-tr from-blue-600 to-indigo-500 text-white'
              : 'bg-gradient-to-tr from-emerald-500 to-teal-700 text-white'
          }`}
        >
          {isUser ? 'YOU' : 'AI'}
        </div>

        <div className="flex flex-col space-y-1">
          <div
            className={`rounded-2xl px-4 py-3 text-sm shadow-md leading-relaxed ${
              isUser
                ? 'bg-blue-600 text-white rounded-tr-none'
                : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-tl-none'
            }`}
          >
            <div className="whitespace-pre-wrap">{message.content}</div>

            {(message.confidence !== undefined || message.leadGrade) && (
              <div className="mt-2.5 flex flex-wrap items-center gap-2 border-t border-slate-700/50 pt-2 text-xs">
                {message.confidence !== undefined && (
                  <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 font-medium text-emerald-400 border border-emerald-500/20">
                    Confidence: {(message.confidence * 100).toFixed(0)}%
                  </span>
                )}
                {message.leadGrade && (
                  <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 font-medium text-amber-400 border border-amber-500/20">
                    Grade {message.leadGrade} Lead
                  </span>
                )}
              </div>
            )}
          </div>
          <span className={`text-[10px] text-slate-400 px-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.createdAt ? new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
          </span>
        </div>
      </div>
    </div>
  );
}