export async function getAuthToken() {
  return localStorage.getItem('jwt_token') || '';
}

export async function apiFetch(url: string, options: RequestInit = {}) {
  let token = await getAuthToken();
  options.headers = {
    ...options.headers,
    'Authorization': 'Bearer ' + token,
  };
  if (options.body && !(options.headers as any)['Content-Type']) {
    (options.headers as any)['Content-Type'] = 'application/json';
  }

  let res = await fetch(url, options);
  if (res.status === 401) {
    localStorage.removeItem('jwt_token');
    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
      window.location.href = '/login';
    }
  }
  return res;
}

export interface Mail {
  mail_id: string;
  google_id: string;
  email?: string;
  subject: string;
  category: string;
  summary?: string;
  snippet?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  toolCalls?: string[];
}
