import React from 'react';
import { Play, Clock, Sparkles } from 'lucide-react';

export default function VideoResult({ result, onJump, isSelected = false }) {
  return (
    <div
      onClick={() => onJump(result)}
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? 'bg-slate-800/95 border-emerald-500 ring-1 ring-emerald-500/50'
          : 'bg-slate-800/40 hover:bg-slate-800/80 border-slate-700/60'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 font-mono text-emerald-400 font-semibold">
              Score: {result.score.toFixed(3)}
            </span>
            <span className="text-xs text-slate-400 font-mono flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>{result.timestamp}</span>
            </span>
          </div>
          <h4 className="text-sm font-semibold text-white mt-1.5 line-clamp-1">
            {result.video_title}
          </h4>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onJump(result);
          }}
          className="shrink-0 flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition-all shadow-md"
        >
          <Play className="w-3 h-3 fill-current" />
          <span>Play</span>
        </button>
      </div>

      <p className="mt-2 text-xs text-slate-300 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800 line-clamp-2">
        {result.text}
      </p>
    </div>
  );
}
