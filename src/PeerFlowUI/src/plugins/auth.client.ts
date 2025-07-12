export default defineNuxtPlugin(() => {
  if (process.client) {
    const globalStore = useGlobalStore();
    
    // Restore user data from localStorage
    const savedUser = localStorage.getItem('peerflow_user');
    const savedAccessToken = localStorage.getItem('peerflow_access_token');
    const savedRefreshToken = localStorage.getItem('peerflow_refresh_token');
    
    if (savedUser && savedAccessToken && savedRefreshToken) {
      try {
        const userData = JSON.parse(savedUser);
        globalStore.setUser(userData);
        globalStore.setTokens(savedAccessToken, savedRefreshToken);
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        // Clear invalid data
        localStorage.removeItem('peerflow_user');
        localStorage.removeItem('peerflow_access_token');
        localStorage.removeItem('peerflow_refresh_token');
      }
    }
  }
});
