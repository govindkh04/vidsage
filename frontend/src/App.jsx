import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SearchBar from './components/SearchBar';
import AnswerCard from './components/AnswerCard';
import CitationCard from './components/CitationCard';
import VideoPlayer from './components/VideoPlayer';
import VideoResult from './components/VideoResult';
import LoadingState from './components/LoadingState';
import { useYouTubePlayer } from './hooks/useYouTubePlayer';
import { askQuestion, searchLectures, getVideos, getHealth } from './services/api';
import { AlertCircle, BookOpen, Sparkles, Video, Search } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('ask');
  const [health, setHealth] = useState(null);
  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Ask State
  const [qaResult, setQaResult] = useState(null);
  const [activeCitation, setActiveCitation] = useState(null);

  // Search State
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // YouTube Player Hook
  const { isReady, seekToTimestamp } = useYouTubePlayer('vidsage-youtube-iframe');

  // Load health & indexed videos on mount
  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.warn('Health check warning:', err));

    getVideos()
      .then((data) => setVideos(data))
      .catch((err) => console.warn('Videos fetch warning:', err));
  }, []);

  // Handle Question Submission
  const handleAskSubmit = async (question) => {
    setIsLoading(true);
    setError(null);
    setQaResult(null);

    try {
      const data = await askQuestion(question);
      setQaResult(data);

      // Auto-load first citation if grounded
      if (data.grounded && data.citations && data.citations.length > 0) {
        const first = data.citations[0];
        setActiveCitation(first);
        seekToTimestamp(first.video_id, first.start_sec, false);
      } else {
        setActiveCitation(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to generate answer. Ensure backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Direct Search Submission
  const handleSearchSubmit = async (query) => {
    setIsLoading(true);
    setError(null);
    setSearchQuery(query);
    setSearchResults([]);

    try {
      const data = await searchLectures(query);
      setSearchResults(data.results || []);

      if (data.results && data.results.length > 0) {
        const first = data.results[0];
        const citationAdapt = {
          title: first.video_title,
          video_id: first.video_id,
          timestamp: first.timestamp,
          start_sec: first.start_sec,
          url: first.source_url,
        };
        setActiveCitation(citationAdapt);
        seekToTimestamp(first.video_id, first.start_sec, false);
      }
    } catch (err) {
      setError(err.message || 'Failed to search lectures.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Citation Click
  const handleJumpToCitation = (citation) => {
    setActiveCitation(citation);
    seekToTimestamp(citation.video_id, citation.start_sec, true);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-3 pt-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>AI-Powered YouTube Lecture Revision Assistant</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Your Videos. Your Knowledge.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
              Instantly.
            </span>
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
            Search inside YouTube lecture playlists. Retrieve the exact concept explanation and jump directly to the verified timestamp.
          </p>
        </div>

        {/* Search Bar */}
        <SearchBar
          mode={activeTab === 'search' ? 'search' : 'ask'}
          onSubmit={activeTab === 'search' ? handleSearchSubmit : handleAskSubmit}
          isLoading={isLoading}
        />

        {/* Error Alert */}
        {error && (
          <div className="max-w-3xl mx-auto p-4 rounded-xl bg-red-950/40 border border-red-800/80 text-red-300 text-sm flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && <LoadingState />}

        {/* Tab 1: Revision Assistant View */}
        {activeTab === 'ask' && !isLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Answer & Citations */}
            <div className="lg:col-span-7 space-y-6">
              {qaResult ? (
                <>
                  <AnswerCard
                    question={qaResult.question}
                    answer={qaResult.answer}
                    grounded={qaResult.grounded}
                    citationsCount={qaResult.citations?.length || 0}
                  />

                  {qaResult.citations && qaResult.citations.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                          <BookOpen className="w-4 h-4 text-emerald-400" />
                          <span>Exact Timestamp Citations ({qaResult.citations.length})</span>
                        </h4>
                        <span className="text-xs text-slate-500">Click to jump in video</span>
                      </div>

                      <div className="space-y-3">
                        {qaResult.citations.map((c, i) => (
                          <CitationCard
                            key={i}
                            citation={c}
                            onJump={handleJumpToCitation}
                            isSelected={activeCitation?.citation_id === c.citation_id}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
                  <div className="w-12 h-12 mx-auto rounded-xl bg-slate-800 flex items-center justify-center text-emerald-400">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-200">Ask Any Question</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Type a question above or click one of the suggested sample questions. VidSage will retrieve the lecture excerpt, generate a grounded answer, and seek the embedded player.
                  </p>
                </div>
              )}
            </div>

            {/* Right Column: Embedded YouTube Video Player */}
            <div className="lg:col-span-5 sticky top-24">
              <VideoPlayer activeCitation={activeCitation} isPlayerReady={isReady} />
            </div>
          </div>
        )}

        {/* Tab 2: Direct Search View */}
        {activeTab === 'search' && !isLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-7 space-y-4">
              {searchResults.length > 0 ? (
                <>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Retrieved {searchResults.length} segments for "{searchQuery}"</span>
                  </div>
                  <div className="space-y-3">
                    {searchResults.map((r, i) => (
                      <VideoResult
                        key={i}
                        result={r}
                        onJump={(item) =>
                          handleJumpToCitation({
                            title: item.video_title,
                            video_id: item.video_id,
                            timestamp: item.timestamp,
                            start_sec: item.start_sec,
                            url: item.source_url,
                          })
                        }
                        isSelected={activeCitation?.start_sec === r.start_sec}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
                  <Search className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm text-slate-400">
                    Enter technical keywords above to perform direct semantic retrieval on indexed transcripts.
                  </p>
                </div>
              )}
            </div>

            <div className="lg:col-span-5 sticky top-24">
              <VideoPlayer activeCitation={activeCitation} isPlayerReady={isReady} />
            </div>
          </div>
        )}

        {/* Tab 3: Indexed Library View */}
        {activeTab === 'library' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white">Indexed Knowledge Base</h2>
                <p className="text-xs text-slate-400">All lectures currently indexed in your Qdrant vector database.</p>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                {videos.length} Lectures Available
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {videos.map((v, i) => (
                <div
                  key={i}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="w-10 h-10 rounded-xl bg-red-500/10 text-red-400 flex items-center justify-center shrink-0">
                      <Video className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {v.chunks_count} chunks
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-white line-clamp-2">{v.title}</h3>
                    <p className="text-xs text-slate-500 font-mono mt-1">ID: {v.video_id}</p>
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <a
                      href={v.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-slate-400 hover:text-white transition-colors"
                    >
                      Watch on YouTube
                    </a>
                    <button
                      onClick={() => {
                        setActiveTab('ask');
                        handleAskSubmit(`What is discussed in "${v.title}"?`);
                      }}
                      className="text-xs px-3 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 font-medium transition-colors"
                    >
                      Ask about lecture
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        <p>VidSage — AI-Powered YouTube Lecture Search & Revision Assistant</p>
      </footer>
    </div>
  );
}
