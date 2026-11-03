import React, { useState } from 'react';
import { Search, ArrowRight, CornerDownLeft, Sparkles } from 'lucide-react';

export default function SearchBar({ onSubmit, isLoading, mode = 'ask' }) {
  const [input, setInput] = useState('');

  const sampleQuestions = [
    "Video schedule aur consistency ke baare me kya bataya gaya hai?",
    "Har din kitne questions aayenge aur festivals me kya schedule rahega?",
    "DSA patterns roadmap for beginners",
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit(input.trim());
    }
  };

  const handlePillClick = (question) => {
    setInput(question);
    onSubmit(question);
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <div className="absolute left-4 pointer-events-none text-slate-400">
          {mode === 'ask' ? (
            <Sparkles className="w-5 h-5 text-emerald-400" />
          ) : (
            <Search className="w-5 h-5 text-slate-400" />
          )}
        </div>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            mode === 'ask'
              ? "Ask in English or Hinglish (e.g. 'Bhai memoization vs tabulation kahan explain kiya hai?')..."
              : "Search technical topics or concepts in transcripts..."
          }
          disabled={isLoading}
          className="w-full pl-12 pr-28 py-4 bg-slate-800/80 hover:bg-slate-800 text-white placeholder-slate-400 rounded-2xl border border-slate-700/80 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none transition-all shadow-xl shadow-black/20 text-base"
        />

        <div className="absolute right-2 flex items-center space-x-1">
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-emerald-500/20"
          >
            <span>{mode === 'ask' ? 'Ask' : 'Search'}</span>
            <CornerDownLeft className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Suggested question pills */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <span className="text-xs font-medium text-slate-400 flex items-center space-x-1">
          <span>Try:</span>
        </span>
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handlePillClick(q)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 hover:text-white transition-all text-left truncate max-w-[280px]"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
