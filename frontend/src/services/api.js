const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse(res) {
  if (!res.ok) {
    let errorMsg = `Server error (${res.status})`;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errorMsg = errData.detail;
      }
    } catch {
      // JSON parse fallback
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function askQuestion(question, topK = null, threshold = null) {
  const payload = { question };
  if (topK !== null) payload.top_k = topK;
  if (threshold !== null) payload.threshold = threshold;

  const res = await fetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function searchLectures(query, topK = 6, videoId = null) {
  const payload = { query, top_k: topK };
  if (videoId) payload.video_id = videoId;

  const res = await fetch(`${API_BASE_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function getVideos() {
  const res = await fetch(`${API_BASE_URL}/videos`);
  return handleResponse(res);
}

export async function getHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(res);
}
