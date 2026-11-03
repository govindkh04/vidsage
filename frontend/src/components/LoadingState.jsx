import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

const MESSAGES = [
  "Searching your indexed lectures with dense vectors...",
  "Retrieving exact timestamp intervals from Qdrant...",
  "Groq LLM is synthesizing your grounded revision answer...",
  "Formatting clickable citations and video timestamps...",
];

export default function LoadingState() {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % MESSAGES.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="py-12 flex flex-col items-center justify-center space-y-4 text-center">
      <div className="relative">
        <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
          <Loader2 className="w-7 h-7 text-emerald-400 animate-spin" />
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-slate-200 transition-all duration-300">
          {MESSAGES[msgIndex]}
        </p>
        <p className="text-xs text-slate-500">Searching transcripts with timestamp fidelity</p>
      </div>
    </div>
  );
}
