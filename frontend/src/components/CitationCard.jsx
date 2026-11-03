import React from 'react';
import { Play, Clock, ExternalLink } from 'lucide-react';

export default function CitationCard({ citation, onJump, isSelected = false }) {
  return (
    <div
      onClick={() => onJump(citation)}
      className={`group relative p-4 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? 'bg-slate-800/95 border-emerald-500 ring-1 ring-emerald-500/50 shadow-lg shadow-emerald-500/10'
          : 'bg-slate-800/50 hover:bg-slate-800 border-slate-700/60 hover:border-slate-600'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left: Badge + Title */}
        <div className="flex items-start gap-2.5">
          <span className="shrink-0 px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 font-mono font-bold text-xs border border-emerald-500/30">
            {citation.citation_id}
          </span>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors line-clamp-1">
              {citation.title}
            </h4>
            <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
              <span className="flex items-center space-x-1 text-emerald-400/90 font-medium font-mono">
                <Clock className="w-3.5 h-3.5" />
                <span>{citation.timestamp}</span>
              </span>
              <span>•</span>
              <span>Starts at {citation.start_sec}s</span>
            </div>
          </div>
        </div>

        {/* Right Action: Play / Jump button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onJump(citation);
          }}
          className={`shrink-0 flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            isSelected
              ? 'bg-emerald-500 text-slate-950 shadow-md'
              : 'bg-slate-700/80 group-hover:bg-emerald-500/20 text-slate-300 group-hover:text-emerald-400 border border-slate-600/50 group-hover:border-emerald-500/30'
          }`}
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{isSelected ? 'Playing' : 'Jump Here'}</span>
        </button>
      </div>

      {/* Transcript excerpt */}
      <p className="mt-3 text-xs text-slate-300/90 leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80 line-clamp-3">
        "{citation.text}"
      </p>

      {/* Direct external link fallback */}
      <div className="mt-2.5 flex items-center justify-end">
        <a
          href={citation.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center space-x-1 transition-colors"
        >
          <span>Open on YouTube</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}
