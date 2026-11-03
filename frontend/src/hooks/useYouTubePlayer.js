import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook to manage the YouTube IFrame Player API lifecycle, video changes, and timestamp seeking.
 */
export function useYouTubePlayer(containerId, initialVideoId = null) {
  const playerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState(initialVideoId);
  const pendingSeekRef = useRef(null);

  useEffect(() => {
    // 1. Ensure YouTube IFrame API script is in the DOM
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }

    let isSubscribed = true;

    const initPlayer = () => {
      if (!isSubscribed || playerRef.current || !window.YT || !window.YT.Player) {
        return;
      }

      playerRef.current = new window.YT.Player(containerId, {
        height: '100%',
        width: '100%',
        videoId: initialVideoId || '',
        playerVars: {
          autoplay: 0,
          modestbranding: 1,
          rel: 0,
          origin: window.location.origin,
        },
        events: {
          onReady: (event) => {
            if (!isSubscribed) return;
            setIsReady(true);
            if (pendingSeekRef.current !== null) {
              const { videoId, seconds } = pendingSeekRef.current;
              pendingSeekRef.current = null;
              if (videoId) {
                event.target.loadVideoById(videoId, seconds);
              } else {
                event.target.seekTo(seconds, true);
              }
              event.target.playVideo();
            }
          },
          onError: (err) => {
            console.error('YouTube Player Error:', err);
          },
        },
      });
    };

    if (window.YT && window.YT.Player) {
      initPlayer();
    } else {
      const prevCallback = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (prevCallback) prevCallback();
        initPlayer();
      };
    }

    return () => {
      isSubscribed = false;
      if (playerRef.current && playerRef.current.destroy) {
        try {
          playerRef.current.destroy();
        } catch {
          // ignore cleanup errors
        }
        playerRef.current = null;
      }
    };
  }, [containerId, initialVideoId]);

  const seekToTimestamp = useCallback((videoId, seconds, autoplay = true) => {
    // Rewind by 5 seconds to provide context before explanation begins
    const targetSeconds = Math.max(0, seconds - 5);

    if (!isReady || !playerRef.current) {
      // Queue action until player is ready
      pendingSeekRef.current = { videoId, seconds: targetSeconds };
      setCurrentVideoId(videoId);
      return;
    }

    try {
      if (currentVideoId !== videoId) {
        setCurrentVideoId(videoId);
        playerRef.current.loadVideoById({
          videoId,
          startSeconds: targetSeconds,
        });
      } else {
        playerRef.current.seekTo(targetSeconds, true);
        if (autoplay) {
          playerRef.current.playVideo();
        }
      }
    } catch (e) {
      console.error('Failed to seek player:', e);
    }
  }, [isReady, currentVideoId]);

  return {
    isReady,
    currentVideoId,
    seekToTimestamp,
  };
}
