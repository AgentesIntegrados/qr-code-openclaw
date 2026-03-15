const AUTH_TOKEN_KEY = 'auth_token';

export const isAuthenticated = () => {
  if (typeof window === 'undefined') return false;
  try {
    const token = sessionStorage.getItem(AUTH_TOKEN_KEY);
    return token !== null;
  } catch {
    return false;
  }
};

export const login = async (username: string, password: string) => {
  try {
    const response = await fetch('/api/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      console.error('Erro na autenticação:', data.error);
      return false;
    }
    
    if (data.token) {
      sessionStorage.setItem(AUTH_TOKEN_KEY, data.token);
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Erro ao fazer login:', error);
    return false;
  }
};

export const logout = () => {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
    console.clear();
    window.location.href = '/login';
  } catch {
    console.error('Erro ao fazer logout');
  }
};
